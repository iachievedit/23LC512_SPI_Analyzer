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

# Operation Modes of the 23A512/23LC512
BYTE_MODE       = 0x00
PAGE_MODE       = 0x02
SEQUENTIAL_MODE = 0x01
RESERVED        = 0x03

# Analyzer states for Byte mode
START      = 0
GET_INS    = 1
GET_ADDR_H = 2
GET_ADDR_L = 3
GET_DATA   = 4

# High level analyzers must subclass the HighLevelAnalyzer class.
class HLA_23LC512_SPI(HighLevelAnalyzer):

  mode_setting = ChoicesSetting(choices=('Sequential', 'Byte', 'Page'))

  result_types = {
    'Instruction': {
      'format': '{{data.instruction}}'
    },
    'Address': {
      'format':  'Address {{data.address}}'
    },
    'Data': {
      'format': 'Data:  {{data.data}}'
    },
    'Mode': {
      'format': '{{data.mode}} Mode'
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
    elif instruction == WRMR_INS:
      return 'Write Mode Register'
    elif instruction == RMDR_INS:
      return 'Read Mode Register'
    else:
      return 'Unknown'

  # Decodes the mode register value, see
  # 2.5 Read Mode Register Instruction of datasheet
  def decode_mode(self, mode_register):
    # Mode value is in Bits 7 and 6
    mode = (mode_register & 0xc0) >> 6
    return mode

  def mode_str(self, mode):
    if mode == BYTE_MODE:
      return 'Byte'
    elif mode == PAGE_MODE:
      return 'Page'
    elif mode == SEQUENTIAL_MODE:
      return 'Sequential'

  def decode(self, frame: AnalyzerFrame):
    # SPI frame types are: enable, result, and disable
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
        self.data        = b''                # Prepare to receive data
          
        if self.instruction in [WRITE_INS, READ_INS]:
          self.state = GET_ADDR_H           # Next byte will be the high byte of the address
        elif self.instruction in [WRMR_INS, RMDR_INS]:
          self.state = GET_DATA             # Next byte will be mode register value

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

        # In Sequential mode we want to accumulate all of the data
        # received in the coming frames
        if self.mode_setting == 'Sequential':
          self.sequential_frame_count = 0

        return AnalyzerFrame('Address', self.address_frame_start, frame.end_time, {
          'address': self.address
        })        

      elif self.state == GET_DATA:          

        if self.instruction == WRITE_INS:

          if self.mode_setting == 'Byte':
            self.data = frame.data['mosi'][0]
            self.data_frame_start = frame.start_time
            self.data_frame_end   = frame.end_time

          elif self.mode_setting == 'Sequential':

            if self.sequential_frame_count == 0:
              self.data_frame_start = frame.start_time

            self.sequential_frame_count += 1
            self.data += frame.data['mosi']
            self.data_frame_end = frame.end_time
  
        elif self.instruction == READ_INS:

          if self.mode_setting == 'Byte':
            self.data = frame.data['miso'][0]
            self.data_frame_start = frame.start_time
            self.data_frame_end   = frame.end_time

          elif self.mode_setting == 'Sequential':

            if self.sequential_frame_count == 0:
              self.data_frame_start = frame.start_time

            self.sequential_frame_count += 1
            self.data += frame.data['miso']
            self.data_frame_end = frame.end_time


        elif self.instruction == WRMR_INS:
          self.data = frame.data['mosi'][0]

          mode = self.decode_mode(self.data)
          return AnalyzerFrame('Mode', frame.start_time, frame.end_time, {
            'mode':  self.mode_str(mode)
          })

        elif self.instruction == RMDR_INS:
          self.data = frame.data['miso'][0]

          mode = self.decode_mode(self.data)
          return AnalyzerFrame('Mode', frame.start_time, frame.end_time, {
            'mode':  self.mode_str(mode)
          })

    elif frame.type == 'disable':

      if self.state == GET_DATA:
        # Return the data frame itself
        return AnalyzerFrame('Data',
          self.data_frame_start,
          self.data_frame_end, {
          'data': self.data
        })
      else:
        # This isn't a valid state
        pass
