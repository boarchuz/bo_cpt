import sys
import argparse
import os
import subprocess
import csv
import tempfile
import re

BO_CPT_BASE =  'BO_CPT_LIST_'
BO_CPT_GUARD =  BO_CPT_BASE + 'H'

# See gen_esp32part.py
APP_TYPE = 0x00
DATA_TYPE = 0x01
FLAGS = {
    'encrypted': 0
}
MIN_PARTITION_SUBTYPE_APP_OTA = 0x10

SUBTYPES = {
    APP_TYPE: {
        'factory': 0x00,
        'test': 0x20,
        'ota_0': MIN_PARTITION_SUBTYPE_APP_OTA + 0,
        'ota_1': MIN_PARTITION_SUBTYPE_APP_OTA + 1,
        'ota_2': MIN_PARTITION_SUBTYPE_APP_OTA + 2,
        'ota_3': MIN_PARTITION_SUBTYPE_APP_OTA + 3,
        'ota_4': MIN_PARTITION_SUBTYPE_APP_OTA + 4,
        'ota_5': MIN_PARTITION_SUBTYPE_APP_OTA + 5,
        'ota_6': MIN_PARTITION_SUBTYPE_APP_OTA + 6,
        'ota_7': MIN_PARTITION_SUBTYPE_APP_OTA + 7,
        'ota_8': MIN_PARTITION_SUBTYPE_APP_OTA + 8,
        'ota_9': MIN_PARTITION_SUBTYPE_APP_OTA + 9,
        'ota_10': MIN_PARTITION_SUBTYPE_APP_OTA + 10,
        'ota_11': MIN_PARTITION_SUBTYPE_APP_OTA + 11,
        'ota_12': MIN_PARTITION_SUBTYPE_APP_OTA + 12,
        'ota_13': MIN_PARTITION_SUBTYPE_APP_OTA + 13,
        'ota_14': MIN_PARTITION_SUBTYPE_APP_OTA + 14,
        'ota_15': MIN_PARTITION_SUBTYPE_APP_OTA + 15,
    },
    DATA_TYPE: {
        'ota': 0x00,
        'phy': 0x01,
        'nvs': 0x02,
        'coredump': 0x03,
        'nvs_keys': 0x04,
        'efuse': 0x05,
        'undefined': 0x06,
        'esphttpd': 0x80,
        'fat': 0x81,
        'spiffs': 0x82,
    },
}

TYPES = {
    'app': APP_TYPE,
    'data': DATA_TYPE,
}

def sanitise_label(label):
    return format(re.sub('[^0-9a-zA-Z]+', '_', label).upper())

def get_val(strval, may_have_suffix=False):
    try:
        return int(strval)
    except ValueError:
        try:
            return int(strval, 16)
        except ValueError:
            if may_have_suffix:
                if len(strval) > 1 and strval[:-1].isdigit() and strval[-1] in "kKmM":
                    return int(strval[:-1]) * (1024 if strval[-1] in "kK" else 1024*1024)
    raise ValueError("invalid value")

def partition_type_val(strval):
    # check for string match
    for pt in TYPES:
        if pt == strval:
            return TYPES[pt]
    # try parse as number
    type_val = get_val(strval)
    if type_val < 0 or type_val > 255:
        raise ValueError("invalid partition type")
    return type_val

def partition_subtype_val(partition_type, strval):
    # check for string match
    for pt in TYPES:
        if TYPES[pt] == partition_type:
            for ps in SUBTYPES[TYPES[pt]]:
                if ps == strval:
                    return SUBTYPES[TYPES[pt]][ps]
    # try parse as number
    type_val = get_val(strval)
    if type_val < 0 or type_val > 255:
        raise ValueError("invalid partition subtype")
    return type_val

def format_partition_csv(partition_info):
    if len(partition_info) != 6:
        raise ValueError("invalid partition entry")
    partition_label = partition_info[0]
    partition_macro = sanitise_label(partition_info[0])
    partition_type = partition_type_val(partition_info[1])
    partition_subtype = partition_subtype_val(partition_type, partition_info[2])
    partition_offset = get_val(partition_info[3])
    partition_size = get_val(partition_info[4], True)
    partition_flags = 0
    for flag_string in partition_info[5].split(':'):
        if len(flag_string) > 0:
            if not flag_string in FLAGS:
                raise ValueError("unknown flag '%s'" % (flag_string))
            for flag,bit in FLAGS.items():
                if(flag_string == flag):
                    partition_flags |= (1 << bit)

    return {
        "macro": partition_macro,
        "label": partition_label,
        "type": partition_type,
        "subtype": partition_subtype,
        "offset": partition_offset,
        "size": partition_size,
        "flags": partition_flags
    }

def filter_csv_comments(csvfile):
    for row in csvfile:
        raw = row.split('#')[0].strip()
        if raw: yield raw

def format_csv_to_partitions(csv_string):
    partitions = []
    reader = csv.reader(filter_csv_comments(csv_string.splitlines()), delimiter=',')
    for row in reader:
        partitions.append(format_partition_csv(row))
    return partitions

def main():
    parser = argparse.ArgumentParser(description='[BO] C Partition Table Generator')
    parser.add_argument('--gen', help='Path to gen_esp32part.py')
    parser.add_argument('--csv', help='Partitions CSV filepath')
    parser.add_argument('--out', help='Output header filepath')
    parser.add_argument('--offset', help='Partition table offset', type=lambda x: int(x,0))
    args = parser.parse_args()

    if not (args.gen and args.csv and args.offset and args.offset):
        print("invalid inputs")
        sys.exit(2)

    if not os.path.isfile(args.csv):
        print("csv not found")
        sys.exit(2)

    if not os.path.isfile(args.gen):
        print("gen_esp32part.py not found")
        sys.exit(2)

    if sys.version_info[0] < 3:
        result = subprocess.check_output(args.gen + ' -q -o ' + str(args.offset) + ' ' + args.csv, shell=True)
        fd, tempfile_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(result)
        result = subprocess.check_output(args.gen + ' -q -o ' + str(args.offset) + ' ' + tempfile_path, shell=True)
        os.remove(tempfile_path)
        csv_string = result.decode('ascii')

    else:
        result = subprocess.run(args.gen + ' -q -o ' + str(args.offset) + ' ' + args.csv, check=True, shell=True, capture_output=True)
        fd, tempfile_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(result.stdout)
        result = subprocess.run(args.gen + ' -q -o ' + str(args.offset) + ' ' + tempfile_path, check=True, shell=True, capture_output=True)
        os.remove(tempfile_path)
        csv_string = result.stdout.decode('ascii')

    partitions = format_csv_to_partitions(csv_string)
    if len(partitions) == 0:
        raise RuntimeError("no partitions parsed")

    output_string = (
        '/* Automatically Generated File */\n'
        '\n'
        '#ifndef ' + BO_CPT_GUARD + '\n'
        '#define ' + BO_CPT_GUARD + '\n'
        '\n'
    )

    # Full Partition Table X Macro
    output_string += '#define ' + BO_CPT_BASE + 'PARTITIONS'
    for partition in partitions:
        output_string += (
            ' \\\n'
            '\tX(' + "%s, \"%s\", %d, %d, %s, %s, %d" % (partition["macro"], partition["label"], partition["type"], partition["subtype"], partition["offset"], partition["size"], partition["flags"]) + ')'
        )
    output_string += (
        '\n'
        '\n'
    )

    # App Partitions X Macro
    output_string += '#define ' + BO_CPT_BASE + 'APP_PARTITIONS'
    for partition in partitions:
        if partition["type"] == APP_TYPE:
            output_string += (
                ' \\\n'
                '\tX(' + "%s, \"%s\", %d, %d, %s, %s, %d" % (partition["macro"], partition["label"], partition["type"], partition["subtype"], partition["offset"], partition["size"], partition["flags"]) + ')'
            )
    output_string += (
        '\n'
        '\n'
    )

    # OTA App Partitions X Macro
    output_string += '#define ' + BO_CPT_BASE + 'OTA_APP_PARTITIONS'
    for partition in partitions:
        if partition["type"] == APP_TYPE and (partition["subtype"] & 0xF0) == MIN_PARTITION_SUBTYPE_APP_OTA:
            output_string += (
                ' \\\n'
                '\tX(' + "%s, \"%s\", %d, %d, %s, %s, %d" % (partition["macro"], partition["label"], partition["type"], partition["subtype"], partition["offset"], partition["size"], partition["flags"]) + ')'
            )
    output_string += (
        '\n'
        '\n'
    )

    # Data Partitions X Macro
    output_string += '#define ' + BO_CPT_BASE + 'DATA_PARTITIONS'
    for partition in partitions:
        if partition["type"] == DATA_TYPE:
            output_string += (
                ' \\\n'
                '\tX(' + "%s, \"%s\", %d, %d, %s, %s, %d" % (partition["macro"], partition["label"], partition["type"], partition["subtype"], partition["offset"], partition["size"], partition["flags"]) + ')'
            )
    output_string += (
        '\n'
        '\n'
    )

    # Define All
    for partition in partitions:
        output_string += (
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_MACRO\t%s' %           partition["macro"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_LABEL\t%s' % 			partition["label"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_TYPE\t(%d)' % 			partition["type"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_SUBTYPE\t(%d)' % 		partition["subtype"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_OFFSET\t(%d)' % 		partition["offset"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_SIZE\t(%d)' % 			partition["size"] +
            '\n#define BO_CPT_PARTITION_' + partition["macro"] + '_FLAGS\t(%d)' % 		partition["flags"]
        )
    output_string += (
        '\n'
        '\n'
    )

    # 2D Array
    output_string += '#define ' + BO_CPT_BASE + 'ARRAY'
    for type in range(0x00, 0xFF + 1):
        output_string += (
            ' \\\n'
            'XX('
        )
        for subtype in range(0x00, 0xFF + 1):
            partition_info = {
                "label": "",
                "macro": "CPT_NONE",
                "type": 0,
                "subtype": 0,
                "offset": 0,
                "size": 0,
                "flags": 0
            }
            for partition in partitions:
                if partition["type"] == type and partition["subtype"] == subtype:
                    partition_info = partition
                    break
            output_string += ('\tX(' + "%s, \"%s\", %d, %d, %s, %s, %d" % (partition_info["macro"], partition_info["label"], partition_info["type"], partition_info["subtype"], partition_info["offset"], partition_info["size"], partition_info["flags"]) + ')')
        output_string += (')')
    output_string += (
        '\n'
        '\n'
    )

    output_string += (
        '#endif /* ' + BO_CPT_GUARD + ' */'
    )

    out_file = open(args.out, 'w')
    out_file.write(output_string)
    out_file.close()

if __name__ == "__main__":
    main()
