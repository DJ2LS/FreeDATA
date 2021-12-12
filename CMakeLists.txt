cmake_minimum_required(VERSION 3.0)
project (FreeDATA)
include(CTest)
enable_testing()

# Find codec2
if(CODEC2_BUILD_DIR)
    find_package(codec2 REQUIRED
        PATHS ${CODEC2_BUILD_DIR}
        NO_DEFAULT_PATH
        CONFIGS codec2.cmake
    )
    if(codec2_FOUND)
        message(STATUS "Codec2 library found in build tree.")
    endif()
else()
    find_package(codec2 REQUIRED)
endif()

# test variables
set(FRAMESPERBURST 3)
set(BURSTS 1)
set(TESTFRAMES 3)

add_test(NAME 001_highsnr_stdio_P_C
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        python3 test_tx.py --mode datac0 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        freedv_data_raw_rx datac0 - - --framesperburst ${FRAMESPERBURST} | hexdump -C")
        set_tests_properties(001_highsnr_stdio_P_C PROPERTIES PASS_REGULAR_EXPRESSION "HELLO WORLD")

add_test(NAME 001_highsnr_stdio_C_P
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        freedv_data_raw_tx datac0 --testframes ${TESTFRAMES} --bursts ${BURSTS} --framesperburst ${FRAMESPERBURST} /dev/zero - |
                        python3 test_rx.py --mode 14 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(001_highsnr_stdio_C_P PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME 001_highsnr_stdio_P_P
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        python3 test_tx.py --mode datac0 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        python3 test_rx.py --mode 14 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(001_highsnr_stdio_P_P PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")
