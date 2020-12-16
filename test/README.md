# TESTS

### TEST_RX.py
--> RX NOT WORKING RIGHT NOW! 
mh... :-/ 



### TEST_TX.py 

Send string "TEST"
```
./TEST_TX.py | ./freedv_data_raw_rx DATAC3 - - | hexdump -C
```
Output should be:
```
payload bytes_per_modem_frame: 30
00000000  54 45 53 54 00 00 00 00  00 00 00 00 00 00 00 00  |TEST............|
modem bufs processed: 22  output bytes: 30 output_frames: 1 
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00        |..............|
0000001e
```
       
       
### Checksum comparison FREEDV vs CRCENGINE       
```
       
       ###################### CHECKSUM COMPARISON FREEDV VS CRCENGINE ########
        #https://crccalc.com
        
        teststring = b'TEST'
        

     
        # freedv crc16 checksum
        crctest2 = c_ushort(self.c_lib.freedv_gen_crc16(teststring, len(teststring)))
        print("FREEDV2: " + str(crctest2.value) + " = " + hex(crctest2.value))      
        
      
        #Python crc16 checksum
        crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library 
        crctest3 = crc_algorithm(teststring)
        print("CRCENGINE: " + str(crctest3) + " = " + hex(crctest3))
        
        
        #######################################################################
```
