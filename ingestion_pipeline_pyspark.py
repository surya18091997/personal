from datetime import datetime

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as f
from pyspark.sql.types import StringType, TimestampType


# Currenly we dont have proper partition logic implemented
# This would be done after confirmation
class IngestionPipeline:
    def __init__(self, config: dict, **kwargs):
        self.config = config
        self._validateConf()
        self.sc.addPyFile(self.config["utilsPath"])
        from utils import athena_refresh_partitions, column_datatype, path_exists

        self.path_exists = path_exists
        self.column_datatype = column_datatype
        self.athena_refresh_partitions = athena_refresh_partitions

    def _validateConf(self):
        """_validateConf Helper method to setup the instance variables
        Takes the config dict from the instance and parse
        """
        _ = [setattr(self, k, v) for k, v in self.config.items()]
        if self.partition_flag == "Y" and "partition_col" not in self.config:
            self.partition_col = "de_created_dt"
            curr_dt = datetime.now()
            self.de_created_dt = int(curr_dt.strftime("%Y%m%d%H%M%S"))
            self.partition_col_dtype = "string"
        if not hasattr(self, "flatten_conf"):
            self.flatten_conf = {
                "skip_arrays": False,
                "skip_structs": False,
                "columns_to_be_skipped": [],
                "columns_to_be_exploded": []
            }
        if not hasattr(self, "cols_to_front"):
            self.cols_to_front = None
        if not hasattr(self, "keep_parent_names"):
            self.keep_parent_names = "Y"
        if not hasattr(self, "rename_col_mapping"):
            self.rename_col_mapping = None

    def castAllColString(self, df: DataFrame) -> DataFrame:
        """castAllColString helps in casting all columns as string
        Args:
            df: spark dataframe for which casting to be applied
        Returns:
            casted dataframe
        """
        return df.select([f.col(c).cast("string") for c in df.columns])

    def readData(self) -> DataFrame:
        """readData reads the data from the specified input path as Dataframe
        Returns:
            spark dataframe with input data
        """
        assert self.inp_file_format in [
            "json",
            "parquet",
            "csv"
        ], f"Invalid file format - {self.inp_file_format}"
        if self.path_exists(self.sc, self.inp_read_path):
            opts = {"mergeSchema": "true"}
            if self.inp_file_format == 'json':
                opts["multiline"] = "true"
            elif self.inp_file_format == 'csv':
                opts["header"] = "true"
            df = getattr(
                self.spark.read.options(**opts),
                self.inp_file_format,
            )(self.inp_read_path)
            if df.columns==['_id', '_doc']:
                df = self.spark.read.option("multiline", "true").json(df.rdd.map(lambda x: x[1]))
            if (
                    self.partition_flag == "Y"
                    and "partition_col" not in self.config.keys()
            ):
                df = df.withColumn("de_created_dt", f.lit(self.de_created_dt))
            return df

    def checkNonFlatCols(self, df: DataFrame) -> bool:
        """Function to check if the dataframe has non flat columns.
        Args:
            df(DataFrame): input dataframe
        Returns:
            array_struct(bool): Whether the dataframe contains
            non flat columns or not"""

        for column in df.dtypes:
            if self.column_datatype(column).startswith("struct") or \
                    self.column_datatype(column).startswith("array"):
                array_struct = True
                break

            else:
                array_struct = False

        return array_struct

    def flattenJson(self, df: DataFrame) -> DataFrame:
        """Flattens the array and struct types in the json data
        Args:
            df(DataFrame): input dataframe
            flatten_conf(dict): dict with config required for flattening
        Returns:
            df(DataFrame): flattened dataframe"""

        columns_to_be_skipped = []
        if self.flatten_conf["skip_arrays"]:
            columns_to_be_skipped.extend(
                [
                    column[0]
                    for column in df.dtypes
                    if self.column_datatype(column).startswith("array")
                ]
            )

        if self.flatten_conf["skip_structs"]:
            columns_to_be_skipped.extend(
                [
                    column[0]
                    for column in df.dtypes
                    if self.column_datatype(column).startswith("struct")
                ]
            )

        if self.flatten_conf["columns_to_be_skipped"]:
            columns_to_be_skipped.extend(
                self.flatten_conf["columns_to_be_skipped"]
            )

        self.log.info(
            f"Columns to be skipped while flattening: "
            f"{columns_to_be_skipped if columns_to_be_skipped else None}"
        )

        for column in df.dtypes:
            column_name = column[0]
            if column_name in columns_to_be_skipped and (
                    self.column_datatype(column).startswith("array<struct")
                    or self.column_datatype(column).startswith("array")
                    or self.column_datatype(column).startswith("struct")
            ):
                df = df.withColumn(
                    column_name,
                    f.to_json(f.col(column_name)).cast(StringType()),
                )
            elif self.column_datatype(column).startswith("array<struct") or (
                self.column_datatype(column).startswith(
                    "array"
                    ) and column_name in self.flatten_conf[
                        "columns_to_be_exploded"
                        ]
            ):
                df = df.withColumn(
                    column_name, f.explode_outer(f.col(column_name))
                )
            elif self.column_datatype(column).startswith("array") \
                    and column_name not in self.flatten_conf[
                "columns_to_be_exploded"
            ]:
                df = df.withColumn(
                    column_name, f.concat_ws(",", f.col(column_name))
                )
            elif self.column_datatype(column).startswith("struct"):
                child_columns = df.select(f"`{column_name}`.*").columns
                for child_column in child_columns:
                    df = df.withColumn(
                        f"{column_name}__{child_column}",
                        f.col(f"`{column_name}`.`{child_column}`"),
                    )
                df = df.drop(column_name)

        if self.checkNonFlatCols(df):
            df = self.flattenJson(df)

        self.log.info("JSON flattening complete")
        return df

    def sortColumns(self, df: DataFrame) -> DataFrame:
        """Sorts the column in alphabetical order for better readability
        Args:
            df(DataFrame): flattened dataframe
        Returns:
            df(DataFrame): flattened dataframe after sorting columns
        """
        if self.cols_to_front:
            self.log.info(f"Column to be moved to front: {self.cols_to_front}")
            remaining_columns = list(
                set([f"`{column}`" for column in df.columns])
                - set([f"`{column}`" for column in self.cols_to_front])
            )
            df = df.select(*self.cols_to_front, *sorted(remaining_columns))
        else:
            df = df.select(sorted(df.columns))
        self.log.info("Column sorting complete")
        return df

    def renameColumnNames(self, df: DataFrame) -> DataFrame:
        """1. Renames the column names based on column_mapping parameter
        2. Renames the flattened column names into readable names if required
        Args:
            df(DataFrame): flattened dataframe
        Returns:
            df(DataFrame): flattened dataframe after renaming
        """

        def replaceSpecialCharacters(column_name):
            """Replaces special characters in the column names
            Args:
                column_name(str): column name in which the special
                characters have to be replaced
            Returns:
                column_name(str): column name after replacing
                special characters
            """

            column_name = (
                column_name.replace("-", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("%", "percent")
                .replace(" ", "_")
                .replace(".", "")
                .replace("$", "")
                .replace("/", "_")
                .lower()
            )
            return column_name

        updated_column_names_dict = {}
        if self.keep_parent_names == "Y":
            for column in df.columns:
                updated_column_names_dict[column] = replaceSpecialCharacters(
                    column.replace("__", "_")
                )
        else:
            self.log.info("Removing parent names from the column names")
            remaining_columns = df.columns
            i = 1
            while remaining_columns:
                innermost_column_name = [
                    "_".join(column.split("__")[-i:]).lower()
                    for column in remaining_columns
                ]
                duplicate_column_names = list(
                    set(
                        [
                            name
                            for name in innermost_column_name
                            if innermost_column_name.count(name) > 1
                        ]
                    )
                )
                temp_list = [
                    x
                    for x in remaining_columns
                    for y in duplicate_column_names
                    if "_".join(x.split("__")[-i:]).lower() == y
                ]
                for column in list(set(remaining_columns) - set(temp_list)):
                    updated_column_names_dict[
                        column
                    ] = replaceSpecialCharacters(
                        "_".join(column.split("__")[-i:])
                    )

                remaining_columns = temp_list
                i += 1
        column_dict = (
            {**(updated_column_names_dict), **(self.rename_col_mapping)}
            if self.rename_col_mapping
            else updated_column_names_dict
        )
        for k, v in column_dict.items():
            df = df.withColumnRenamed(k, v)
        self.log.info("Column renaming complete")
        return df

    def _deltaDeleteLoad(
            self, df: DataFrame, op_path: str, join_col: list
    ) -> None:
        """_deltaDeleteLoad implements the delete and load using delta table
        Args:
            df: initial/incremental dataframe
            op_path: output s3 path for write delta table
            join_col: column(s) which must be used for deleting in delta table
        """
        join_cond = ""
        for column in join_col:
            join_cond = (
                    join_cond + "delta." + column + " = " + "updates." + column
            )
            if column != join_col[-1]:
                join_cond = join_cond + " and "
        if self.path_exists(self.sc, op_path):
            delta_data = DeltaTable.forPath(self.spark, op_path)
            delta_data.alias("delta").merge(
                df.alias("updates"), join_cond
            ).whenMatchedDelete().execute()
            delta_data.vacuum(0)
            if self.partition_flag == "Y":
                df.write.format("delta").partitionBy(
                    self.partition_col
                ).option("mergeSchema", "true").mode("append").save(op_path)
            else:
                df.write.format("delta").option("mergeSchema", "true").mode(
                    "append"
                ).save(op_path)
        else:
            if self.partition_flag == "Y":
                df.write.format("delta").partitionBy(self.partition_col).mode(
                    "append"
                ).save(op_path)
            else:
                df.write.format("delta").mode("append").save(op_path)

    def _writeData(
        self,
        df: DataFrame,
        op_path: str,
        op_filetype: str,
        write_mode: str
    ) -> None:
        """_writeData implements write to s3 path in append/overwrite mode
        Args:
            df: dataframe which has to be written to s3
            op_path: output s3 path
            op_filetype: output file type parquet/json/csv
            write_mode: used to control the data append or overwrite in s3
        """
        if self.path_exists(self.sc, op_path):
            opts = {"mergeSchema": "true"}
        else:
            write_mode = "overwrite"
            opts = {"overwriteSchema": "true"}
        if self.partition_flag == "Y" and "partition_col" not in self.config:
            df.write.format(op_filetype).partitionBy("de_created_dt").mode(
                write_mode
            ).options(**opts).save(op_path)
        elif self.partition_flag == "Y" and "partition_col" in self.config:
            df.write.format(op_filetype).partitionBy(self.partition_col).mode(
                write_mode
            ).options(**opts).save(op_path)
        elif self.partition_flag == "N":
            df.write.format(op_filetype).mode(write_mode).options(**opts).save(
                op_path
            )

    def _writeDeltaUpsert(
            self, df: DataFrame, op_path: str, join_cols: list
    ) -> None:
        """_writeDeltaUpsert implements delta format upsert must be used for id
                specific update and insert
        Args:
            df: input dataframe for which upsert has to be done
            op_path: output s3 path
            join_cols: list of columns used for joining
        """
        join_cond = ""
        for column in join_cols:
            join_cond = (
                    join_cond + "delta." + column + " = " + "updates." + column
            )
            if column != join_cols[-1]:
                join_cond = join_cond + " and "
        if self.path_exists(self.sc, op_path):
            delta_data = DeltaTable.forPath(self.spark, op_path)
            delta_data.alias("delta").merge(
                df.alias("updates"), join_cond
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
            delta_data.vacuum(0)
        else:
            df.write.format("delta").mode("overwrite").save(op_path)

    def writeOutput(self, df: DataFrame) -> DataFrame:
        """writeOutput implements the write of dataframe object to s3 path
        Args:
            df: input dataframe
        Returns:
            input dataframe passed after writing the output
        """
        assert self.op_filetype in [
            "parquet",
            "json",
            "csv",
            "delta",
        ], "Invalid output_file_type"
        assert self.op_write_mode in [
            "overwrite",
            "append",
            "upsert",
            "delete_load",
        ], "Invalid output_write_type"
        if self.config.get("custom_datatype", False) and self.op_write_mode in ("append", "csv"):
            table_struc = self.spark.sql(
                f"""SELECT * FROM
                 {self.athena_db_name}.{self.athena_table_name} WHERE 1 = 2
                """
            )
            new_columns = list(set(df.dtypes) - set(table_struc.dtypes))
            table_cols = table_struc.columns
            for col, dtype in new_columns:
                if col in table_cols:
                    raise Exception(f"{col} datatype change occured to {dtype}")
        if self.op_filetype in [
            "parquet",
            "json",
            "csv",
        ] and self.op_write_mode in [
            "overwrite",
            "append",
        ]:
            self._writeData(
                df, self.op_path, self.op_filetype, self.op_write_mode
            )

        if self.op_filetype == "delta" and self.op_write_mode == "upsert":
            self._writeDeltaUpsert(df, self.op_path, self.join_cols)

        if self.op_filetype == "delta" and self.op_write_mode == "delete_load":
            self._deltaDeleteLoad(df, self.op_path, self.join_cols)
        return df

    def _createTable(
            self, table_dtypes: list, db: str, table_name: str, op_path: str
    ) -> None:
        """_createTable implements athena DDL logic drop and create table
        Args:
            table_cols: list of column names from the dataframe
            db: Athena db name
            table_name: Athena table name
            op_path: s3 path where file exists
        """
        if self.partition_flag == "Y":
            table_dtypes = [(x,y) for x,y in table_dtypes if x!=self.partition_col]
        query_str = ""
        query_format = "{table_col} {table_dtype}," if self.config.get("custom_datatype",False) else "{table_col} string,"
        for table_col, table_dtype in table_dtypes:
            query_str += query_format.format(table_col=table_col,table_dtype=table_dtype)
        self.spark.sql(f"DROP TABLE IF EXISTS {db}.{table_name}")
        if self.partition_flag == "Y":
            self.spark.sql(
                f"""CREATE EXTERNAL TABLE {db}.{table_name}
                    ({query_str[:-1]})
                    PARTITIONED BY
                     ({self.partition_col} {self.partition_col_dtype})
                    STORED AS PARQUET
                    LOCATION '{op_path}'
                    """
            )
        else:
            self.spark.sql(
                f"""CREATE EXTERNAL TABLE {db}.{table_name}
                    ({query_str[:-1]})
                    STORED AS PARQUET
                    LOCATION '{op_path}'
                    """
            )
        self.spark.sql(f"REFRESH TABLE {db}.{table_name}")

    def athenaTableDDL(self, df: DataFrame) -> None:
        """athenaTableDDL create table if not exists and helps in checking
            if there are any new columns added to the dataframe
        Args:
            df: Dataframe incremental/full for which table has to be
                created new or column changes that has to be made
        """
        df_cols = df.columns
        df_dtypes = df.dtypes
        if not self.spark._jsparkSession.catalog().tableExists(
                self.athena_db_name, self.athena_table_name
        ):
            self._createTable(
                df_dtypes,
                self.athena_db_name,
                self.athena_table_name,
                self.op_path,
            )
        else:
            table_struc = self.spark.sql(
                f"""SELECT * FROM
                 {self.athena_db_name}.{self.athena_table_name} WHERE 1 = 2
                """
            )
            new_columns = list(set(df_cols) - set(table_struc.columns))
            if new_columns:
                final_cols_dtype = df_dtypes + [
                    i for i in table_struc.dtypes if i[0] in new_columns
                ]
                self._createTable(
                    final_cols_dtype,
                    self.athena_db_name,
                    self.athena_table_name,
                    self.op_path,
                )

    def athenaRefreshPartitions(self) -> None:
        """athenaRefreshPartitions helper method to setup the athena_conf
        and call the athena_refresh_partitions method
        """
        athena_conf = [
            [
                self.athena_db_name,
                self.athena_table_name,
                self.op_path.split("/")[2],
                '/'.join(self.op_path.split("/")[3:]),
                self.partition_col
            ]
        ]
        self.athena_refresh_partitions(
            self.sc,
            self.utilsPath,
            self.region,
            self.athena_s3_staging_dir,
            athena_conf,
            self.log
        )

    def dateCast(self, df: DataFrame) -> DataFrame:
        """Cast date column which are not in date format to datetime formats"""
        df_cols = df.columns
        for conf in self.config.get("date_cast_conf", []):
            column, conversion = conf["column"], conf["conversion"]
            if column not in df_cols:
                continue
            if conversion=="mongo":
                df = df.withColumn(column, f.from_unixtime(f.col(column) / 1000).cast(TimestampType()))
        return df
