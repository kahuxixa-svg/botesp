#include "troko_timer.h"

#include "application.h"

#include <esp_log.h>

namespace {
constexpr const char* kTag = "TrokoTimer";
}

void TrokoTimer::Initialize(Display* display) {
    display_ = display;
    esp_timer_create_args_t args = {};
    args.callback = [](void* arg) {
        auto* self = static_cast<TrokoTimer*>(arg);
        Application::GetInstance().Schedule([self]() { self->Expire(); });
    };
    args.arg = this;
    args.name = "troko_reminder";
    ESP_ERROR_CHECK(esp_timer_create(&args, &timer_));

    auto& mcp = McpServer::GetInstance();
    mcp.AddTool(
        "self.troko.timer.start",
        "Start one local visual reminder or countdown, from 1 second to 24 hours. "
        "Works offline; lost on reboot. Rejects a second active timer. No sound or Telegram.",
        PropertyList({Property("seconds", kPropertyTypeInteger, 1, 86400),
                      Property("message", kPropertyTypeString).SetMaxLength(160)}),
        [this](const PropertyList& properties) -> ToolResult {
            auto message = properties["message"].value<std::string>();
            if (message.empty()) {
                return std::unexpected("The reminder message cannot be empty");
            }
            if (!Start(properties["seconds"].value<int>(), message)) {
                return std::unexpected("A timer is already active; cancel it first");
            }
            return Status();
        });
    mcp.AddTool("self.troko.timer.status", "Get the local timer and remaining seconds.",
                PropertyList(), [this](const PropertyList&) { return Status(); });
    mcp.AddTool("self.troko.timer.cancel", "Cancel the local reminder or focus timer.",
                PropertyList(), [this](const PropertyList&) -> ToolResult {
                    Cancel();
                    return true;
                });
    mcp.AddTool("self.troko.focus.start",
                "Start a 25-minute focus session with a visual end notice.", PropertyList(),
                [this](const PropertyList&) -> ToolResult {
                    if (!Start(25 * 60, "Concentracion terminada. Descansa 5 minutos.")) {
                        return std::unexpected("A timer is already active; cancel it first");
                    }
                    return Status();
                });
}

bool TrokoTimer::Start(int seconds, const std::string& message) {
    if (deadline_us_ != 0) {
        return false;
    }
    message_ = message;
    deadline_us_ = esp_timer_get_time() + static_cast<int64_t>(seconds) * 1000000;
    ESP_ERROR_CHECK(esp_timer_start_once(timer_, static_cast<uint64_t>(seconds) * 1000000));
    display_->ShowNotification("Temporizador: " + std::to_string(seconds) + " s", 4000);
    ESP_LOGI(kTag, "Visual timer started: %d seconds", seconds);
    return true;
}

void TrokoTimer::Cancel() {
    if (deadline_us_ == 0) {
        return;
    }
    // The one-shot timer may already have fired and queued Expire().
    // Clearing the deadline also invalidates that queued work.
    esp_timer_stop(timer_);
    deadline_us_ = 0;
    message_.clear();
    display_->ShowNotification("Temporizador cancelado", 3000);
    ESP_LOGI(kTag, "Visual timer cancelled");
}

void TrokoTimer::Expire() {
    // A stale callback from a cancelled/replaced timer cannot finish a new one.
    if (deadline_us_ == 0 || esp_timer_get_time() < deadline_us_) {
        return;
    }
    deadline_us_ = 0;
    display_->SetEmotion("happy");
    display_->ShowNotification(message_, 30000);
    display_->SetChatMessage("assistant", message_.c_str());
    message_.clear();
    ESP_LOGI(kTag, "Visual timer finished");
}

ToolResult TrokoTimer::Status() const {
    auto* status = cJSON_CreateObject();
    if (status == nullptr) {
        return std::unexpected("Insufficient memory");
    }
    cJSON_AddBoolToObject(status, "active", deadline_us_ != 0);
    auto remaining =
        deadline_us_ == 0 ? 0 : (deadline_us_ - esp_timer_get_time() + 999999) / 1000000;
    cJSON_AddNumberToObject(status, "remaining_seconds", remaining > 0 ? remaining : 0);
    cJSON_AddStringToObject(status, "message", message_.c_str());
    cJSON_AddBoolToObject(status, "persistent", false);
    return status;
}

void TrokoTimer::ToggleFocus() {
    if (deadline_us_ != 0) {
        Cancel();
    } else {
        Start(25 * 60, "Concentracion terminada. Descansa 5 minutos.");
    }
}

void TrokoTimer::StartDemo() {
    if (!Start(5, "Prueba completada: temporizador y pantalla listos.")) {
        display_->ShowNotification("Ya hay un temporizador activo", 3000);
    }
}
