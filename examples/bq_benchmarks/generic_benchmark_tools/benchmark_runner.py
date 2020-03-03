# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from google.cloud import bigquery

from load_benchmark_tools import load_table_benchmark
from generic_benchmark_tools import bucket_util
from query_benchmark_tools import federated_query_benchmark


class BenchmarkRunner:
    """Contains methods for processing and creating load tables for benchmarks.

    Attributes:
        bq_project(str): ID of the project that holds the BigQuery dataset
            and benchmark tables.
        gcs_project(str):  ID of the project that holds the GCS bucket
            where the files to be loaded are stored.
        staging_project(str_: ID of the project that contains the
            staging tables that the files to be loaded into the benchmark table
            were generated from.
        staging_dataset_id(str): ID of the dataset that contains the
            staging tables that the files to be loaded into the benchmark table
            were generated from.
        dataset_id(str): ID of the dataset that the benchmark tables should
            be loaded into.
        bucket_name(str): Name of the GCS bucket that holds the files that
            should be loaded into the benchmark table.
        bucket_util(load_benchmark_tools.bucket_util.BucketUtil): Helper class for
            interacting with the bucket that the holds the files that
            should be loaded into the benchmark table.
        results_table_name(str): Name of the BigQuery table that the
            benchmark table's load results will be inserted into.
        results_table_dataset_id(str): Name of the BigQuery dataset that the
            benchmark table's load results will be inserted into.
        duplicate_benchmark_tables(bool): Boolean value to determine what to
            do if a benchmark table already exists for a given file
            combination. If True, TableProcessor knows to create another
            benchmark table with the same combination to increase the
            number of results for accuracy. If not, TablesProcessor knows
            to only create a benchmark table for a given combination if one
            has not yet been created.
        file_params(dict): Dictionary containing each file parameter and
            its possible values.
        bq_logs_dataset(str): Name of dataset hold BQ logs table.

    """

    def __init__(
            self,
            bq_project,
            gcs_project,
            staging_project,
            staging_dataset_id,
            dataset_id,
            bucket_name,
            results_table_name,
            results_table_dataset_id,
            duplicate_benchmark_tables,
            file_params,
            bq_logs_dataset,
            run_federated_query_benchmark=False,
            include_federated_query_benchmark=False
    ):
        self.bq_project = bq_project
        self.gcs_project = gcs_project
        self.staging_project = staging_project
        self.staging_dataset_id = staging_dataset_id
        self.dataset_id = dataset_id
        self.bucket_name = bucket_name
        self.bucket_util = bucket_util.BucketUtil(
            bucket_name=self.bucket_name,
            project_id=self.gcs_project,
            file_params=file_params,
        )
        self.results_table_name = results_table_name
        self.results_table_dataset_id = results_table_dataset_id
        self.duplicate_benchmark_tables = duplicate_benchmark_tables
        self.bq_logs_dataset = bq_logs_dataset
        self.run_federated_query_benchmark = run_federated_query_benchmark
        self.include_federated_query_benchmark = \
            include_federated_query_benchmark
        self.files_to_skip = set()

    def execute_file_loader_benchmark(self):
        # Gather files combinations that already have benchmark tables.
        files_with_benchmark_tables = self._gather_files_with_benchmark_tables()
        if not self.duplicate_benchmark_tables:
            self.files_to_skip = files_with_benchmark_tables
        self._create_tables(files_with_benchmark_tables)

    def execute_federated_query_benchmark(self):
        # Gather files combinations that already have benchmark tables.
        files_with_benchmark_tables = self._gather_files_with_benchmark_tables()
        self._create_tables(files_with_benchmark_tables)

    def _gather_files_with_benchmark_tables(self):
        """Generates file combinations that already have benchmark tables.

        Creates a set of files that already have been loaded to create
        benchmark tables. Generates list by querying the job.sourceURI field
        from the results table.
        Returns:
            Set of file names that already have been loaded to create
            benchmark tables.
        """
        query = (
            'SELECT loadProperties.sourceURI FROM `{0:s}.{1:s}.{2:s}` '.format(
                self.bq_project,
                self.results_table_dataset_id,
                self.results_table_name,
            )
        )
        query_job = bigquery.Client().query(
            query,
            location='US',
        )
        files_with_benchmark_tables = set()
        for row in query_job:
            if row['sourceURI'] and self.bucket_name in row['sourceURI']:
                uri = row['sourceURI'].split('gs://{0:s}/'.format(
                    self.bucket_name
                ))[1]
                file_name = uri.split('/*')[0]
                files_with_benchmark_tables.add(file_name)
        return files_with_benchmark_tables

    def _create_tables(self, files_with_benchmark_tables):
        """Creates a benchmark table for each file combination in GCS bucket.
        """
        # Gather file combinations that exist in the GCS Bucket.
        existing_paths = self.bucket_util.get_existing_paths(
            run_federated_query_benchmark=self.run_federated_query_benchmark
        )
        # Create a benchmark table for each existing file combination, and
        # load the data from the file into the benchmark table.
        for path in existing_paths:
            path = path.split('/')
            path = '/'.join(path[:len(path) - 1])
            if path not in self.files_to_skip:
                if path in files_with_benchmark_tables:
                    verb = 'Duplicating'
                else:
                    verb = 'Processing'
                logging.info('{0:s} benchmark table for {1:s}'.format(
                    verb,
                    path,
                ))
                table = load_table_benchmark.LoadTableBenchmark(
                    bq_project=self.bq_project,
                    gcs_project=self.gcs_project,
                    staging_project=self.staging_project,
                    staging_dataset_id=self.staging_dataset_id,
                    dataset_id=self.dataset_id,
                    bucket_name=self.bucket_name,
                    path=path,
                    results_table_name=self.results_table_name,
                    results_table_dataset_id=self.results_table_dataset_id,
                    bq_logs_dataset=self.bq_logs_dataset
                )
                table_name = table.create_table()
                table.load_from_gcs()
                if self.run_federated_query_benchmark or \
                        self.include_federated_query_benchmark:
                    self._run_federated_query(
                        table_name,
                        path
                    )
                table.delete_table()

    def _run_federated_query(self, table_name, path):
        # use loaded table to run a federated query benchmark
        uri = 'gs://{0:s}/{1:s}'.format(self.bucket_name, path)
        query_benchmark = federated_query_benchmark \
            .FederatedQueryBenchmark(
                bq_project=self.bq_project,
                gcs_project=self.gcs_project,
                dataset_id=self.dataset_id,
                bq_logs_dataset_id=self.bq_logs_dataset,
                native_table_id=table_name,
                bucket_name=self.bucket_name,
                file_uri=uri,
                results_table_name=self.results_table_name,
                results_table_dataset_id=self.results_table_dataset_id
            )
        logging.info(
            'Running Federated Query Benchmark for BQ managed '
            'table {0:s} and file {1:s}'.format(
                table_name,
                uri
            ))
        query_benchmark.run_queries()