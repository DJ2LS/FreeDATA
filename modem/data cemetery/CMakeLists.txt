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

add_test(NAME audio_buffer
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_audiobuffer.py")
         set_tests_properties(audio_buffer PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

add_test(NAME resampler
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_resample_48_8.py")
        set_tests_properties(resampler PROPERTIES PASS_REGULAR_EXPRESSION "PASS")

add_test(NAME modem_state_machine
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_modem_states.py")
         set_tests_properties(modem_state_machine PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

add_test(NAME modem_irs_iss
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_modem.py")
         set_tests_properties(modem_irs_iss PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

# disabled this test as its actually broken since we introduced session IDs
#add_test(NAME chat_text
#         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
#                        export PYTHONPATH=../modem;
#                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
#                        python3 test_chat_text.py")
#         set_tests_properties(chat_text PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

add_test(NAME datac13_frames
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_datac13.py")
         set_tests_properties(datac13_frames PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

# disabled this test as its actually broken since we introduced dataclasses
#add_test(NAME datac13_frames_negative
#         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
#                        export PYTHONPATH=../modem;
#                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
#                        python3 test_datac13_negative.py")
#         set_tests_properties(datac13_frames_negative PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

add_test(NAME helper_routines
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_helpers.py")
         set_tests_properties(helper_routines PROPERTIES PASS_REGULAR_EXPRESSION "errors: 0")

add_test(NAME py_highsnr_stdio_P_P_multi
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        export BURSTS=${BURSTS};
                        export FRAMESPERBURST=${FRAMESPERBURST};
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_highsnr_stdio_P_P_multi.py")
        set_tests_properties(py_highsnr_stdio_P_P_multi PROPERTIES PASS_REGULAR_EXPRESSION "DATAC13: ${BURSTS}/${FRAMESPERBURST} DATAC1: ${BURSTS}/${FRAMESPERBURST} DATAC3: ${BURSTS}/${FRAMESPERBURST}")

add_test(NAME py_highsnr_stdio_P_P_datacx
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        export BURSTS=${BURSTS};
                        export FRAMESPERBURST=${FRAMESPERBURST};
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_highsnr_stdio_P_P_datacx.py")
        set_tests_properties(py_highsnr_stdio_P_P_datacx PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME py_highsnr_stdio_P_C_datacx
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        export BURSTS=${BURSTS};
                        export FRAMESPERBURST=${FRAMESPERBURST};
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_highsnr_stdio_P_C_datacx.py")
        set_tests_properties(py_highsnr_stdio_P_C_datacx PROPERTIES PASS_REGULAR_EXPRESSION "HELLO WORLD")

add_test(NAME py_highsnr_stdio_C_P_datacx
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        export PYTHONPATH=../modem;
                        export BURSTS=${BURSTS};
                        export FRAMESPERBURST=${FRAMESPERBURST};
                        export TESTFRAMES=${TESTFRAMES};
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 test_highsnr_stdio_C_P_datacx.py")
        set_tests_properties(py_highsnr_stdio_C_P_datacx PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME highsnr_stdio_P_C_single
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 util_tx.py --mode datac13 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        sox -t .s16 -r 48000 -c 1 - -t .s16 -r 8000 -c 1 - |
                        freedv_data_raw_rx datac13 - - --framesperburst ${FRAMESPERBURST} | hexdump -C")
        set_tests_properties(highsnr_stdio_P_C_single PROPERTIES PASS_REGULAR_EXPRESSION "HELLO WORLD")

add_test(NAME highsnr_stdio_C_P_single
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        freedv_data_raw_tx datac13 --testframes ${TESTFRAMES} --bursts ${BURSTS} --framesperburst ${FRAMESPERBURST} /dev/zero - |
                        sox -t .s16 -r 8000 -c 1 - -t .s16 -r 48000 -c 1 - |
                        python3 util_rx.py --mode datac13 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(highsnr_stdio_C_P_single PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME highsnr_stdio_P_P_single
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 util_tx.py --mode datac13 --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        python3 util_rx.py --debug --mode datac13 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS}")
        set_tests_properties(highsnr_stdio_P_P_single PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: ${BURSTS} RECEIVED FRAMES: ${FRAMESPERBURST}")

add_test(NAME highsnr_stdio_P_P_multi
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        python3 util_multimode_tx.py --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
                        python3 util_multimode_rx.py --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} --timeout 60")
        set_tests_properties(highsnr_stdio_P_P_multi PROPERTIES PASS_REGULAR_EXPRESSION "DATAC13: ${BURSTS}/${FRAMESPERBURST} DATAC1: ${BURSTS}/${FRAMESPERBURST} DATAC3: ${BURSTS}/${FRAMESPERBURST}")

# These tests can't run on GitHub actions as we don't have a virtual sound card
if(NOT DEFINED ENV{GITHUB_RUN_ID})

# uses aplay/arecord then pipe to Python
add_test(NAME highsnr_virtual1_P_P_single_alsa
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual1.sh")
       set_tests_properties(highsnr_virtual1_P_P_single_alsa PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 5 RECEIVED FRAMES: 10 RX_ERRORS: 0")

# let Python do audio I/O
add_test(NAME highsnr_virtual2_P_P_single
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual2.sh")
       set_tests_properties(highsnr_virtual2_P_P_single PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

# Multimode test with Python I/O
add_test(NAME highsnr_virtual3_P_P_multi
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual_mm.sh")
       set_tests_properties(highsnr_virtual3_P_P_multi PROPERTIES PASS_REGULAR_EXPRESSION "DATAC13: 2/4 DATAC1: 2/4 DATAC3: 2/4")

# let Python do audio I/O via pyaudio callback mode
add_test(NAME highsnr_virtual4_P_P_single_callback
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual3a.sh")
       set_tests_properties(highsnr_virtual4_P_P_single_callback PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

# let Python do audio I/O via pyaudio callback mode with code outside of callback
add_test(NAME highsnr_virtual4_P_P_single_callback_outside
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual3b.sh")
       set_tests_properties(highsnr_virtual4_P_P_single_callback_outside PROPERTIES PASS_REGULAR_EXPRESSION "RECEIVED BURSTS: 3 RECEIVED FRAMES: 6 RX_ERRORS: 0")

# let Python do audio I/O via pyaudio callback mode with code outside of callback
add_test(NAME highsnr_virtual5_P_P_multi_callback
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual4a.sh")
       set_tests_properties(highsnr_virtual5_P_P_multi_callback PROPERTIES PASS_REGULAR_EXPRESSION "DATAC13: 2/4 DATAC1: 2/4 DATAC3: 2/4")

# let Python do audio I/O via pyaudio callback mode with code outside of callback
add_test(NAME highsnr_virtual5_P_P_multi_callback_outside
         COMMAND sh -c "export LD_LIBRARY_PATH=${CODEC2_BUILD_DIR}/src;
                        PATH=$PATH:${CODEC2_BUILD_DIR}/src;
                        cd ${CMAKE_CURRENT_SOURCE_DIR}/test;
                        ./test_virtual4b.sh")
       set_tests_properties(highsnr_virtual5_P_P_multi_callback_outside PROPERTIES PASS_REGULAR_EXPRESSION "DATAC13: 2/4 DATAC1: 2/4 DATAC3: 2/4")

endif()

