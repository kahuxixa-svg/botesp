#pragma once

#include <driver/gpio.h>

// LILYGO T-Display-S3 1.9-inch ST7789, parallel 8080 interface.
// https://github.com/Xinyuan-LilyGO/T-Display-S3/tree/main/examples/factory
#define DISPLAY_POWER_PIN GPIO_NUM_15
#define DISPLAY_BACKLIGHT_PIN GPIO_NUM_38
#define DISPLAY_RD_PIN GPIO_NUM_9
#define DISPLAY_WR_PIN GPIO_NUM_8
#define DISPLAY_DC_PIN GPIO_NUM_7
#define DISPLAY_CS_PIN GPIO_NUM_6
#define DISPLAY_RST_PIN GPIO_NUM_5
#define DISPLAY_DATA_PINS                                \
    {GPIO_NUM_39, GPIO_NUM_40, GPIO_NUM_41, GPIO_NUM_42, \
     GPIO_NUM_45, GPIO_NUM_46, GPIO_NUM_47, GPIO_NUM_48}

// Portrait orientation rotated 180 degrees: USB connector and buttons at the top.
#define DISPLAY_WIDTH 170
#define DISPLAY_HEIGHT 320
#define DISPLAY_OFFSET_X 35
#define DISPLAY_OFFSET_Y 0
#define DISPLAY_SWAP_XY false
#define DISPLAY_MIRROR_X true
#define DISPLAY_MIRROR_Y true

#define BOOT_BUTTON_GPIO GPIO_NUM_0
#define USER_BUTTON_GPIO GPIO_NUM_14
