#pragma once

#include "display/lcd_display.h"

// Original, unmodified Troko GIFs, scaled proportionally to fit the display.
class TrokoEyesDisplay : public SpiLcdDisplay {
public:
    using SpiLcdDisplay::SpiLcdDisplay;
    ~TrokoEyesDisplay() override;
    void SetupUI() override;
    bool SetEmotion(const char* emotion) override;
    void SetTheme(Theme* theme) override;
    void SetStatus(const char* status) override;
    void UpdateStatusBar(bool update_all = false) override;
    void CycleExpression();

private:
    unsigned preview_index_ = 0;
    bool thinking_ = false;
    lv_timer_t* idle_timer_ = nullptr;
    uint32_t idle_since_ = 0;
    uint32_t next_idle_change_ = 12000;
    unsigned idle_step_ = 0;
    bool showing_scene_ = false;
    void FitEyes();
    void StyleHeader();
    void IdleTick();
    void ResetIdle();
};
