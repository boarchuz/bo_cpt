# ESP-IDF C Partition Table

CPT is an ESP-IDF component to create a C header version of the partition table.

See the example for usage.

## Notes
* Do a full clean and rebuild after any changes to the partition table to ensure an updated header is generated
* A very large macro representing the partition table as a 2D array is generated, therefore:
    - Opening the file may be very slow
    - Take care that any occurrences of this macro can be optimised out
