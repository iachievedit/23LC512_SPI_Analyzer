# 23LC512 SPI Analyzer

This is version 0.0.1 of a Saleae Logic Analyzer extension to decode SPI messages sent to and from a Microchip <a href="https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/23A512-23LC512-512-Kbit-SPI-Serial-SRAM-with-SDI-and-SQI-Interface-20005155C.pdf">23LC512</a> (or 23A512) 512-Kbit SPI Serial SRAM.

This chip supports three different modes:

* Byte
* Page
* Sequential

Version 0.0.2 of this analyzer supports _only_ decoding **Byte** mode.  Future modes will be supported.
  
## 0.0.2

* Only Byte mode supported for decoding writes and reads
* Decoding **Write** instruction supported
* Decoding **Read** instruction supported
* Decoding **Write Mode Register** instruction
* Decoding **Read Mode Register** instruction

Examples:

**Write Byte**

![](writeByte.png)

**Read Byte**

![](readByte.png)

**Write Mode Register**

![](writeModeRegister.png)

**Read Mode Register**

![](readModeRegister.png)




## 0.0.1

* Initial version
* **Byte** mode supported
* Decoding **Write** instruction supported
* Decoding **Read** instruction supported



## 0.0.3 Plans

* Support for **Sequential** mode decoding


  