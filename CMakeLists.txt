if(CONFIG_BO_CPT_DIR_DO_NOT_USE_CMAKE_VAR)
    set(requires )
else()
    set(requires partition_table)
endif()

set(include_dirs
    .
    "${CMAKE_CURRENT_BINARY_DIR}"
)

idf_component_register(
    INCLUDE_DIRS "${include_dirs}"
    REQUIRES "${requires}"
)

if(CONFIG_BO_CPT_DIR_DO_NOT_USE_CMAKE_VAR)
    if(CONFIG_PARTITION_TABLE_CUSTOM)
        # bootloader has different project_dir so user must provide config to locate project_dir and/or partition table csv:
        if(CONFIG_BO_CPT_DIR_IN_COMPONENTS)
            set(project_dir ${CMAKE_CURRENT_SOURCE_DIR}../../../)
        elseif(CONFIG_BO_CPT_DIR_RELATIVE_PROJECT_PATH)
            set(project_dir ${CMAKE_CURRENT_SOURCE_DIR}${CONFIG_BO_CPT_PROJECT_PATH})
        else()
            set(project_dir ${CONFIG_BO_CPT_PROJECT_PATH})
        endif()

        # Custom filename expands any path relative to the project
        get_filename_component(BO_CPT_PARTITION_CSV_PATH "${CONFIG_PARTITION_TABLE_FILENAME}" ABSOLUTE BASE_DIR "${project_dir}")
    else()
        # Other .csv files are in the partition_table component directory
        get_filename_component(BO_CPT_PARTITION_CSV_PATH "${IDF_PATH}/components/partition_table/${CONFIG_PARTITION_TABLE_FILENAME}" ABSOLUTE)
    endif()
else()
    set(BO_CPT_PARTITION_CSV_PATH ${PARTITION_CSV_PATH})
endif()

if(NOT EXISTS "${BO_CPT_PARTITION_CSV_PATH}")
    # this should be FATAL_ERROR however this prevents menuconfig initialisation // TODO
    message(WARNING "Partition table CSV file ${BO_CPT_PARTITION_CSV_PATH} not found.")
endif()

set(out_file "${CMAKE_CURRENT_BINARY_DIR}/bo_cpt_list.h")
add_custom_target(
    bo_cpt_gen
    DEPENDS ${out_file}
)
add_dependencies(${COMPONENT_LIB} bo_cpt_gen)

set(gen_py_path ${IDF_PATH}/components/partition_table/gen_esp32part.py)
if(NOT EXISTS "${gen_py_path}")
    message(FATAL_ERROR "${gen_py_path} not found.")
endif()

add_custom_command(
    OUTPUT ${out_file}
    DEPENDS ${BO_CPT_PARTITION_CSV_PATH}
    COMMAND ${CMAKE_COMMAND} -E echo "BO_CPT: generating partition config @ ${out_file}"
    COMMAND ${python} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/bo_cpt_gen.py --gen ${gen_py_path} --csv ${BO_CPT_PARTITION_CSV_PATH} --offset ${CONFIG_PARTITION_TABLE_OFFSET} --out "${out_file}"
)
