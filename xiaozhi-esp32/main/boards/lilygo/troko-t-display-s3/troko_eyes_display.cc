#include "troko_eyes_display.h"

#include "application.h"
#include "assets/lang_config.h"

#include <esp_log.h>
#include <esp_random.h>
#include <algorithm>
#include <cstring>

TrokoEyesDisplay::~TrokoEyesDisplay() {
    DisplayLockGuard lock(this);
    if (idle_timer_)
        lv_timer_delete(idle_timer_);
}

void TrokoEyesDisplay::FitEyes() {
    if (!emoji_box_)
        return;
    lv_obj_set_size(emoji_box_, width_, height_);
    lv_obj_set_style_radius(emoji_box_, 0, 0);
    lv_obj_set_style_bg_color(emoji_box_, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(emoji_box_, LV_OPA_COVER, 0);
    lv_obj_remove_flag(emoji_box_, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_remove_flag(emoji_box_, LV_OBJ_FLAG_OVERFLOW_VISIBLE);
    if (emoji_image_) {
        // The panel owns orientation for every expression and idle scene.
        // Reset image transforms when replacing a GIF of a different size.
        lv_image_set_rotation(emoji_image_, 0);
        lv_obj_set_style_transform_rotation(emoji_image_, 0, LV_PART_MAIN);
        lv_obj_center(emoji_image_);
        // Fit both the original square eyes and the portrait idle scenes without
        // cropping, stretching or overlapping the clock.
        int image_width = gif_controller_ ? gif_controller_->width() : 240;
        int image_height = gif_controller_ ? gif_controller_->height() : 240;
        if (image_width > 0 && image_height > 0) {
            int scale =
                std::min((width_ - 8) * 256 / image_width, (height_ - 48) * 256 / image_height);
            lv_image_set_scale(emoji_image_, scale);
        }
    }
}

void TrokoEyesDisplay::StyleHeader() {
    if (top_bar_) {
        lv_obj_set_style_bg_color(top_bar_, lv_color_black(), 0);
        lv_obj_set_style_bg_opa(top_bar_, LV_OPA_COVER, 0);
    }
    // Keep the clock overlay transparent so the status icons remain visible.
    if (status_bar_)
        lv_obj_set_style_bg_opa(status_bar_, LV_OPA_TRANSP, 0);
    for (auto* label :
         {status_label_, notification_label_, network_label_, mute_label_, battery_label_}) {
        if (label)
            lv_obj_set_style_text_color(label, lv_color_white(), 0);
    }
}

void TrokoEyesDisplay::SetupUI() {
    SpiLcdDisplay::SetupUI();
    DisplayLockGuard lock(this);
    FitEyes();
    StyleHeader();
    if (!idle_timer_) {
        ResetIdle();
        idle_timer_ = lv_timer_create(
            [](lv_timer_t* timer) {
                static_cast<TrokoEyesDisplay*>(lv_timer_get_user_data(timer))->IdleTick();
            },
            500, this);
    }
    ESP_LOGI("TrokoEyes", "Portrait renderer ready: 21 original expressions + 5 idle scenes");
}

void TrokoEyesDisplay::SetTheme(Theme* theme) {
    SpiLcdDisplay::SetTheme(theme);
    DisplayLockGuard lock(this);
    FitEyes();
    StyleHeader();
}

bool TrokoEyesDisplay::SetEmotion(const char* emotion) {
    if (!emotion || !*emotion)
        return false;
    DisplayLockGuard lock(this);
    const char* name = emotion;
    if (std::strcmp(name, "robot_2") == 0)
        name = "neutral";
    if (std::strcmp(name, "gear") == 0)
        name = "thinking";
    if (std::strcmp(name, "error") == 0)
        name = "confused";
    if (std::strcmp(name, "listening") == 0)
        name = "relaxed";
    if (std::strcmp(name, "scared") == 0)
        name = "shocked";
    if (std::strcmp(name, "neutral") == 0 && thinking_)
        name = "thinking";
    bool shown = SpiLcdDisplay::SetEmotion(name);
    if (shown) {
        showing_scene_ = false;
        ResetIdle();
        FitEyes();
    }
    return shown;
}

void TrokoEyesDisplay::ResetIdle() {
    idle_since_ = lv_tick_get();
    next_idle_change_ = 12000;
    idle_step_ = 0;
}

void TrokoEyesDisplay::IdleTick() {
    // LVGL invokes this callback under its recursive display mutex. Only UI is
    // changed here; network, timers and application state remain untouched.
    bool idle = Application::GetInstance().GetDeviceState() == kDeviceStateIdle;
    bool overlay =
        (preview_image_ && !lv_obj_has_flag(preview_image_, LV_OBJ_FLAG_HIDDEN)) ||
        (notification_label_ && !lv_obj_has_flag(notification_label_, LV_OBJ_FLAG_HIDDEN));
    if (!idle || overlay) {
        ResetIdle();
        if (showing_scene_) {
            showing_scene_ = false;
            SpiLcdDisplay::SetEmotion("neutral");
            FitEyes();
        }
        return;
    }
    if (lv_tick_get() - idle_since_ < next_idle_change_)
        return;

    static constexpr const char* scenes[] = {"idle_dog", "idle_rocket", "idle_fish", "idle_juggle",
                                             "idle_sleep"};
    static constexpr const char* expressions[] = {"relaxed",   "happy",     "winking",  "cool",
                                                  "thinking",  "funny",     "loving",   "silly",
                                                  "confident", "surprised", "laughing", "neutral"};
    bool scene = idle_step_ % 2 == 0;
    const char* name =
        scene ? scenes[idle_step_ / 2]
              : expressions[esp_random() % (sizeof(expressions) / sizeof(*expressions))];
    bool shown = SpiLcdDisplay::SetEmotion(name);
    showing_scene_ = scene && shown;
    FitEyes();
    idle_since_ = lv_tick_get();
    next_idle_change_ = scene ? 12000 : 8000;
    idle_step_ = (idle_step_ + 1) % 10;
    if (shown)
        ESP_LOGI("TrokoEyes", "Idle animation: %s", name);
    else
        ESP_LOGW("TrokoEyes", "Idle animation unavailable: %s", name);
}

void TrokoEyesDisplay::UpdateStatusBar(bool update_all) {
    SpiLcdDisplay::UpdateStatusBar(update_all);
    DisplayLockGuard lock(this);
    // A tiny status glyph can look like a stray white pixel on this panel.
    // During idle keep only the clock; retain the icons for setup/reconnection.
    bool idle = Application::GetInstance().GetDeviceState() == kDeviceStateIdle;
    for (auto* label : {network_label_, mute_label_, battery_label_}) {
        if (!label)
            continue;
        if (idle)
            lv_obj_add_flag(label, LV_OBJ_FLAG_HIDDEN);
        else
            lv_obj_remove_flag(label, LV_OBJ_FLAG_HIDDEN);
    }
}

void TrokoEyesDisplay::SetStatus(const char* status) {
    SpiLcdDisplay::SetStatus(status);
    DisplayLockGuard lock(this);
    thinking_ = status && std::strcmp(status, Lang::Strings::CONNECTING) == 0;
}

void TrokoEyesDisplay::CycleExpression() {
    static constexpr const char* names[] = {
        "neutral",  "relaxed",     "thinking",  "happy", "laughing", "loving", "cool",
        "winking",  "surprised",   "shocked",   "angry", "sad",      "crying", "sleepy",
        "confused", "embarrassed", "confident", "funny", "silly",    "kissy",  "delicious"};
    unsigned index;
    {
        DisplayLockGuard lock(this);
        index = preview_index_++ % (sizeof(names) / sizeof(names[0]));
    }
    if (SetEmotion(names[index])) {
        ShowNotification(std::string("Gesto Troko: ") + names[index], 2000);
        ESP_LOGI("TrokoEyes", "Playing original animation: %s", names[index]);
    }
}
