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

add_test(NAME 000_resampler
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/000_resampler;
                        python3 t48_8_short.py")
        set_tests_properties(000_resampler PROPERTIES PASS_REGULAR_EXPRESSION "PASS")

add_test(NAME 001_highsnr_stdio_P_C_SM
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        python3 test_tx.py --mode datac0 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        sox -t .s16 -r 48000 -c 1 - -t .s16 -r 8000 -c 1 - |
                        freedv_data_raw_rx datac0 - - --framesperburst ${FRAMESPERBURST} | hexdump -C")
        set_tests_properties(001_highsnr_stdio_P_C_SM PROPERTIES PASS_REGULAR_EXPRESSION "HELLO WORLD")

add_test(NAME 001_highsnr_stdio_C_P_SM
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        freedv_data_raw_tx datac0 --testframes ${TESTFRAMES} --bursts ${BURSTS} --framesperburst ${FRAMESPERBURST} /dev/zero - |
                        sox -t .s16 -r 8000 -c 1 - -t .s16 -r 48000 -c 1 - |
                        python3 test_rx.py --mode datac0 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(001_highsnr_stdio_C_P_SM PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME 001_highsnr_stdio_P_P_SM
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        python3 test_tx.py --mode datac0 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        python3 test_rx.py --mode datac0 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(001_highsnr_stdio_P_P_SM PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")
        
add_test(NAME 001_highsnr_stdio_P_P_MM
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        python3 test_multimode_tx.py --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        python3 test_multimode_rx.py --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} --timeout 20")
        set_tests_properties(001_highsnr_stdio_P_P_MM PROPERTIES PASS_REGULAR_EXPRESSION "DATAC0: ${BURSTS}/${FRAMESPERBURST} DATAC1: ${BURSTS}/${FRAMESPERBURST} DATAC3: ${BURSTS}/${FRAMESPERBURST}")


# These tests can't run on GitHub actions
if(NOT DEFINED ENV{GITHUB_RUN_ID})

# uses aplay/arecord then pipe to Python
add_test(NAME 001_highsnr_virtual1_P_P
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        ./test_virtual1.sh")
       set_tests_properties(001_highsnr_virtual1_P_P PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 5 RECEIVED FRAMES: 10 RX_ERRORS: 0")

# let Python do audio I/O
add_test(NAME 001_highsnr_virtual2_P_P
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        ./test_virtual2.sh")
       set_tests_properties(001_highsnr_virtual2_P_P PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

# Multimode test with Python I/O
add_test(NAME 001_highsnr_virtual3_P_P_MM
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        ./test_virtual_mm.sh")
       set_tests_properties(001_highsnr_virtual3_P_P_MM PROPERTIES PASS_REGULAR_EXPRESSION "DATAC0: 2/4 DATAC1: 2/4 DATAC3: 2/4")

# let Python do audio I/O via pyaudio callback mode
add_test(NAME 001_highsnr_virtual4_P_P_SM_CB
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        ./test_virtual3a.sh")
       set_tests_properties(001_highsnr_virtual4_P_P_SM_CB PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

# let Python do audio I/O via pyaudio callback mode with code outside of callback
add_test(NAME 001_highsnr_virtual4_P_P_SM_CB_OUTSIDE
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                        ./test_virtual3b.sh")
       set_tests_properties(001_highsnr_virtual4_P_P_SM_CB_OUTSIDE PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

endif()
       
