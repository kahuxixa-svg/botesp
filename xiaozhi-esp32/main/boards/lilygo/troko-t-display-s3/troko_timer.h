#pragma once

#include "display.h"
#include "mcp_server.h"

#include <esp_timer.h>
#include <string>

// One local, non-persistent reminder/focus timer. All state belongs to the
// application task; the ESP timer callback only schedules work on that task.
class TrokoTimer {
public:
    void Initialize(Display* display);
    void ToggleFocus();
    void StartDemo();

private:
    Display* display_ = nullptr;
    esp_timer_handle_t timer_ = nullptr;
    int64_t deadline_us_ = 0;
    std::string message_;

    bool Start(int seconds, const std::string& message);
    void Cancel();
    void Expire();
    ToolResult Status() const;
};
