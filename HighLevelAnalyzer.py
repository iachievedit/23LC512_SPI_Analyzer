#
# Copyright (c) 2023 iAchieved.it LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, ChoicesSetting

# See 23A512/23LC512 datasheet, INSTRUCTION SET
WRITE_INS = b'\x02'
READ_INS  = b'\x03'
RMDR_INS  = b'\x05'
WRMR_INS  = b'\x01'

# Analyzer states for Byte mode
START      = 0
GET_INS    = 1
GET_ADDR_H = 2
GET_ADDR_L = 3
GET_DATA   = 4

# High level analyzers must subclass the HighLevelAnalyzer class.
class HLA_23LC512_SPI(HighLevelAnalyzer):

  mode_setting = ChoicesSetting(choices=('Byte', 'Page', 'Sequential'))

  result_types = {
    'Instruction': {
      'format': '{{data.instruction}}'
    },
    'Address': {
      'format':  'Address {{data.address}}'
    },
    'Data': {
      'format': 'Data:  {{data.data}}'
    }
  }

  def __init__(self):
    '''
    Initialize HLA.
    '''

    state = START

  def instruction_str(self, instruction):
    if instruction == WRITE_INS:
      return 'Write'
    elif instruction == READ_INS:
      return 'Read'
    else:
      return 'Unknown'

  def decode(self, frame: AnalyzerFrame):
    # SPI frame types are: enable, result, 
    # enable
    # result
    # disable

    # A frame type of 'enable' triggers our state machine
    if frame.type == 'enable':
      self.state = GET_INS
    elif frame.type == 'result':
      if self.state == GET_INS:

        self.instruction = frame.data['mosi'] # Our instruction will be on the MOSI line
        self.address     = None               # Prepare to receive address
        self.data        = None               # Prepare to receive data
          
        self.state = GET_ADDR_H           # Next byte will be the high byte of the address

        return AnalyzerFrame('Instruction', frame.start_time, frame.end_time, {
          'instruction': self.instruction_str(self.instruction)
        })

      elif self.state == GET_ADDR_H:

        self.address = int.from_bytes(frame.data['mosi'], 'big') << 8
        self.address_frame_start = frame.start_time

        self.state = GET_ADDR_L           # Next byte will be the low byte of the address

      elif self.state == GET_ADDR_L:

        self.address = self.address | int.from_bytes(frame.data['mosi'], 'big')

        self.state = GET_DATA

        return AnalyzerFrame('Address', self.address_frame_start, frame.end_time, {
          'address': self.address
        })        

      elif self.state == GET_DATA:

        if self.instruction == WRITE_INS:
          self.data = frame.data['mosi']
        elif self.instruction == READ_INS:
          self.data = frame.data['miso']

        # Return the data frame itself
        return AnalyzerFrame('Data', frame.start_time, frame.end_time, {
            'data': self.data
        })
