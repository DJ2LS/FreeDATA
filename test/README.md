       
       ./TEST_TX.py | ./freedv_data_raw_rx DATAC3 - -
       
       
       
       
       
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
