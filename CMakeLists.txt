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

add_test(NAME 000_audio_tests
         COMMAND sh -c "cd ${CMAKE_CURRENT_SOURCE_DIR}/test/000_audio_tests;
                            python3 sinustest.py")
add_test(NAME 001_highsnr_stdio_audio
         COMMAND sh -c "cd ${CMAKE_CURRENT_SOURCE_DIR}/test/001_highsnr_stdio_audio;
                            python3 test_tx.py --mode 12 --delay 500 --frames 2 --bursts 1 > t.s16")

