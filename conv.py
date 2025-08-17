# Convort a file encoded in CP437 (old DOS) to UTF-8

# Example:
# python conv.py "2022-01-01_2022-12-31.SE" "2022-01-01_2022-12-31.txt"

import sys
import os
import ctypes
import conv_bertil

def test():

   numOfArguments = len(sys.argv)-1

   if numOfArguments==2:
      # Check that input file exists first
      if os.path.exists(sys.argv[1]):
         print('File ' + sys.argv[1] + ' exists.')
         ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'xxx', 1)
         conv1.conv(sys.argv[1], sys.argv[2])
      else:
         print('*** ConvFromCP437: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
         ctypes.windll.user32.MessageBoxW(0,
            '*** ConvFromCP437: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
            'xxx', 1)
   else: print('2 arguments were expected but '+str(numOfArguments)+ ' were found.')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

test()
