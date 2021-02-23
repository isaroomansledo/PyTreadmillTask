# Sets up the Tindie's PMW3360 Motion Sensor in a PyBoard (for using with PyControl d-series boards)

# order of operation:
# 1: power up (datasheet section 7)
# 2: SROM file download (section 5)
# 3: go for Burst mode (section 4)


def PMW3360_power_up():
    