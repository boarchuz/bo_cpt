#include "esp_log.h"
#include "esp_flash_partitions.h"
#include "esp_partition.h"

#include "bo_cpt.h"

static const char *TAG = "cpt_usage";

#ifndef ARRAY_SIZE
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#endif

static void usage_example_1(void)
{
    // Define and initialise a custom partition table overview
    typedef struct {
        const char *label;
        uint32_t offset;
        uint32_t size;
    } my_partition_info_t;

    const my_partition_info_t partitions[] = {
        #define X(_macro, _label, _type, _subtype, _offset, _size, _flags) \
        {                                                              \
            .label = _label,                                           \
            .offset = _offset,                                         \
            .size = _size,                                             \
        },
        BO_CPT_LIST_PARTITIONS
        #undef X
    };

    ESP_LOGI(TAG, "%u partitions:", ARRAY_SIZE(partitions));
    for (int i = 0; i < ARRAY_SIZE(partitions); ++i)
    {
        ESP_LOGI(TAG, "\t%s @ 0x%08X (0x%X bytes)", partitions[i].label, partitions[i].offset, partitions[i].size);
    }
}

static void usage_example_2(void)
{
    // Initialise an array of esp_partition_info_t of app partitions
    const esp_partition_info_t app_partitions[] = {
        #define X(_macro, _label, _type, _subtype, _offset, _size, _flags) \
        {                                                              \
            .type = _type,                                             \
            .subtype = _subtype,                                       \
            .pos = {                                                   \
                .offset = _offset,                                     \
                .size = _size,                                         \
            },                                                         \
            .label = _label,                                           \
            .flags = _flags,                                           \
        },
        BO_CPT_LIST_APP_PARTITIONS
        #undef X
    };

    ESP_LOGI(TAG, "%u app partitions", ARRAY_SIZE(app_partitions));
    for (int i = 0; i < ARRAY_SIZE(app_partitions); ++i)
    {
        if (app_partitions[i].subtype == PART_SUBTYPE_FACTORY)
        {
            ESP_LOGI(TAG, "Factory app partition @ 0x%08X (%sEncrypted)", app_partitions[i].pos.offset, app_partitions[i].flags & PART_FLAG_ENCRYPTED ? "" : "Not ");
            break;
        }
    }
};

static void usage_example_3(void)
{
    // Check for the existence and validity of a partition at compile time
    #ifdef BO_CPT_PARTITION_FACTORY_LABEL
        #if BO_CPT_PARTITION_FACTORY_TYPE != PART_TYPE_APP || BO_CPT_PARTITION_FACTORY_SUBTYPE != PART_SUBTYPE_FACTORY
            #error "Invalid factory app partition type/subtype"
        #endif
        ESP_LOGI(TAG, "Factory app partition exists");
    #else
        ESP_LOGW(TAG, "No factory app partition");
    #endif
}

static void usage_example_4(void)
{
    // Conveniently initialise an esp_partition_info_t using the partition label
    #define TO_STRING2(x) #x
    #define TO_STRING(x) TO_STRING2(x)
    #define PARTITION_LABEL_TO_INFO(_macro)                                                                \
    {                                                                                                      \
        .type = BO_CPT_PARTITION_##_macro##_TYPE,                                                          \
        .subtype = BO_CPT_PARTITION_##_macro##_SUBTYPE,                                                    \
        .pos = {                                                                                           \
            .offset = BO_CPT_PARTITION_##_macro##_OFFSET,                                                  \
            .size = BO_CPT_PARTITION_##_macro##_SIZE,                                                      \
        },                                                                                                 \
        .label = TO_STRING(BO_CPT_PARTITION_##_macro##_LABEL), .flags = BO_CPT_PARTITION_##_macro##_FLAGS, \
    }

    #ifdef BO_CPT_PARTITION_NVS_LABEL
        const esp_partition_info_t nvs_partition = PARTITION_LABEL_TO_INFO(NVS);
        ESP_LOGI(TAG, "NVS partition size: %u", nvs_partition.pos.size);
    #else
        ESP_LOGW(TAG, "No NVS partition");
    #endif

    #ifdef BO_CPT_PARTITION_OTA_0_LABEL
        const esp_partition_info_t ota0_partition = PARTITION_LABEL_TO_INFO(OTA_0);
        ESP_LOGI(TAG, "OTA0 partition size: %u", ota0_partition.pos.size);
    #else
        ESP_LOGW(TAG, "No OTA0 partition");
    #endif
}

static void usage_example_5(void)
{
    // Use 2D Array
    const esp_partition_info_t partition_table_array[][256] = {
        #define XX(x) {x},
        #define X(_macro, _label, _type, _subtype, _offset, _size, _flags) \
            { \
                .type = _type, \
                .subtype = _subtype, \
                .pos = { \
                    .offset = _offset, \
                    .size = _size \
                }, \
                .label = _label, \
                .flags = _flags, \
            },
        BO_CPT_LIST_ARRAY
        #undef X
        #undef XX
    };

    if(partition_table_array[ESP_PARTITION_TYPE_DATA][ESP_PARTITION_SUBTYPE_DATA_OTA].pos.offset != 0)
    {
        ESP_LOGI(TAG, "OTA data partition size: 0x%X", partition_table_array[ESP_PARTITION_TYPE_DATA][ESP_PARTITION_SUBTYPE_DATA_OTA].pos.size);
    }
    else
    {
        ESP_LOGW(TAG, "No OTA data partition in array");
    }

    const uint32_t total_partitioned_size = 0
        #define XX(x) x
        #define X(_macro, _label, _type, _subtype, _offset, _size, _flags) \
            + _size
        BO_CPT_LIST_ARRAY
        #undef X
        #undef XX
    ;
    ESP_LOGI(TAG, "Total Partitioned: 0x%X", total_partitioned_size);
}

void app_main(void)
{
    usage_example_1();
    usage_example_2();
    usage_example_3();
    usage_example_4();
    usage_example_5();
}
