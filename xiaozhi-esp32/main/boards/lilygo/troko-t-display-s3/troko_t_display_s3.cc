#include "application.h"
#include "audio_codec.h"
#include "backlight.h"
#include "button.h"
#include "config.h"
#include "display/lcd_display.h"
#include "troko_eyes_display.h"
#include "troko_timer.h"
#include "wifi_board.h"

#include <driver/gpio.h>
#include <esp_lcd_io_i80.h>
#include <esp_lcd_panel_ops.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

namespace {
constexpr const char* kTag = "TrokoTDisplayS3";

// No I2S peripheral or external pin is touched in this bring-up variant.
// Pace discarded playback so startup prompts cannot cause a busy loop.
class SilentAudioCodec : public AudioCodec {
public:
    SilentAudioCodec() {
        input_sample_rate_ = 16000;
        output_sample_rate_ = 24000;
    }

private:
    int Read(int16_t* dest, int samples) override {
        vTaskDelay(pdMS_TO_TICKS(20));
        return 0;
    }

    int Write(const int16_t* data, int samples) override {
        auto ticks = pdMS_TO_TICKS(samples * 1000 / output_sample_rate_);
        vTaskDelay(ticks > 0 ? ticks : 1);
        return samples;
    }
};
}  // namespace

class TrokoTDisplayS3 : public WifiBoard {
private:
    Button boot_button_{BOOT_BUTTON_GPIO};
    Button user_button_{USER_BUTTON_GPIO};
    TrokoEyesDisplay* display_ = nullptr;
    TrokoTimer timer_;

    void InitializeDisplay() {
        gpio_config_t outputs = {};
        outputs.pin_bit_mask = (1ULL << DISPLAY_POWER_PIN) | (1ULL << DISPLAY_RD_PIN);
        outputs.mode = GPIO_MODE_OUTPUT;
        ESP_ERROR_CHECK(gpio_config(&outputs));
        ESP_ERROR_CHECK(gpio_set_level(DISPLAY_POWER_PIN, 1));
        ESP_ERROR_CHECK(gpio_set_level(DISPLAY_RD_PIN, 1));
        vTaskDelay(pdMS_TO_TICKS(20));

        esp_lcd_i80_bus_handle_t bus = nullptr;
        esp_lcd_i80_bus_config_t bus_config = {};
        bus_config.dc_gpio_num = DISPLAY_DC_PIN;
        bus_config.wr_gpio_num = DISPLAY_WR_PIN;
        bus_config.clk_src = LCD_CLK_SRC_DEFAULT;
        const gpio_num_t data_pins[] = DISPLAY_DATA_PINS;
        for (size_t i = 0; i < 8; ++i) {
            bus_config.data_gpio_nums[i] = data_pins[i];
        }
        bus_config.bus_width = 8;
        bus_config.max_transfer_bytes = DISPLAY_WIDTH * 20 * sizeof(uint16_t);
        bus_config.dma_burst_size = 64;
        ESP_ERROR_CHECK(esp_lcd_new_i80_bus(&bus_config, &bus));

        esp_lcd_panel_io_handle_t io = nullptr;
        esp_lcd_panel_io_i80_config_t io_config = {};
        io_config.cs_gpio_num = DISPLAY_CS_PIN;
        io_config.pclk_hz = 16 * 1000 * 1000;
        io_config.trans_queue_depth = 10;
        io_config.lcd_cmd_bits = 8;
        io_config.lcd_param_bits = 8;
        io_config.dc_levels.dc_data_level = 1;
        // SpiLcdDisplay's LVGL adapter already swaps RGB565 bytes.
        ESP_ERROR_CHECK(esp_lcd_new_panel_io_i80(bus, &io_config, &io));

        esp_lcd_panel_handle_t panel = nullptr;
        esp_lcd_panel_dev_config_t panel_config = {};
        panel_config.reset_gpio_num = DISPLAY_RST_PIN;
        panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB;
        panel_config.bits_per_pixel = 16;
        ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io, &panel_config, &panel));
        ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
        ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
        // LILYGO's LCD_MODULE_CMD_1 settings for the newer 1.9-inch module.
        // Source: T-Display-S3/examples/factory/factory.ino (MIT).
        struct PanelCommand {
            uint8_t command;
            uint8_t data[14];
            size_t size;
        };
        static constexpr PanelCommand commands[] = {
            {0x3A, {0x05}, 1},
            {0xB2, {0x0B, 0x0B, 0x00, 0x33, 0x33}, 5},
            {0xB7, {0x75}, 1},
            {0xBB, {0x28}, 1},
            {0xC0, {0x2C}, 1},
            {0xC2, {0x01}, 1},
            {0xC3, {0x1F}, 1},
            {0xC6, {0x13}, 1},
            {0xD0, {0xA7}, 1},
            {0xD0, {0xA4, 0xA1}, 2},
            {0xD6, {0xA1}, 1},
            {0xE0,
             {0xF0, 0x05, 0x0A, 0x06, 0x06, 0x03, 0x2B, 0x32, 0x43, 0x36, 0x11, 0x10, 0x2B, 0x32},
             14},
            {0xE1,
             {0xF0, 0x08, 0x0C, 0x0B, 0x09, 0x24, 0x2B, 0x22, 0x43, 0x38, 0x15, 0x16, 0x2F, 0x37},
             14},
        };
        for (const auto& command : commands) {
            ESP_ERROR_CHECK(
                esp_lcd_panel_io_tx_param(io, command.command, command.data, command.size));
        }
        ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel, true));
        ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));

        // Despite its historical name, this adapter also supports i80 panel IO.
        display_ = new TrokoEyesDisplay(io, panel, DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_OFFSET_X,
                                        DISPLAY_OFFSET_Y, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y,
                                        DISPLAY_SWAP_XY);
        GetBacklight()->RestoreBrightness();
        ESP_LOGI(kTag, "ST7789 i80 ready: portrait 170x320, USB at top; external audio disabled");
    }

    void InitializeButtons() {
        boot_button_.OnClick([this]() {
            Application::GetInstance().Schedule([this]() {
                display_->ShowNotification("Audio pendiente: INMP441 + MAX98357A", 4000);
            });
        });
        boot_button_.OnLongPress([this]() { EnterWifiConfigMode(); });
        user_button_.OnClick([this]() {
            Application::GetInstance().Schedule([this]() { display_->CycleExpression(); });
        });
        user_button_.OnDoubleClick(
            [this]() { Application::GetInstance().Schedule([this]() { timer_.StartDemo(); }); });
        user_button_.OnLongPress(
            [this]() { Application::GetInstance().Schedule([this]() { timer_.ToggleFocus(); }); });
    }

public:
    TrokoTDisplayS3() {
        InitializeDisplay();
        timer_.Initialize(display_);
        InitializeButtons();
    }

    AudioCodec* GetAudioCodec() override {
        static SilentAudioCodec codec;
        return &codec;
    }

    Display* GetDisplay() override { return display_; }

    Backlight* GetBacklight() override {
        static PwmBacklight backlight(DISPLAY_BACKLIGHT_PIN, false);
        return &backlight;
    }
};

DECLARE_BOARD(TrokoTDisplayS3);
