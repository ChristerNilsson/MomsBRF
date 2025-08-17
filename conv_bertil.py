# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import sys
import os
import ctypes

def conv(infile: object, outfile: object) -> None:

   print("Decoding a file encoded in CP437")
   print('Reading from "'+infile+'".')
   sie_file = open(infile, "rb")
   fileContent = sie_file.read()
   sie_file.close()
   # print("File content:")
   # print(fileContent)
   decoded_text = fileContent.decode('cp437')
   # print(decoded_text)  # Output: Hello, World! ?

   print("Writing decoded text to file " + outfile + ".")
   txt_file = open(outfile, "wb")
   bytes_data = decoded_text.encode('utf-8')
   txt_file.write(bytes_data)
   txt_file.close()


def test(pfilename):

   if len(sys.argv)>1:
      # Check that file exists first
      if os.path.exists(sys.argv[1]):
         print('File ' + sys.argv[1] + ' exists.')
         ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'baliseCompileXs', 1)
         test(sys.argv[1])
      else:
         print('*** baliseCompile: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
         ctypes.windll.user32.MessageBoxW(0,
            '*** baliseCompile: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
            'baliseCompileXs', 1)
   else: print('No arguments were provided.')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
