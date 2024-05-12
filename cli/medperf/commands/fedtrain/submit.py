import os

import medperf.config as config
from medperf.entities.fedtrain import FederatedTraining
from medperf.exceptions import InvalidEntityError
from medperf.utils import remove_path
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from medperf.comms.entity_resources import resources


class SubmitFederatedTraining:
    @classmethod
    def run(
        cls,
        fedtrain_info: dict,
        no_cache: bool = True,
        # skip_data_preparation_step: bool = False,
    ):
        """Submits a new cube to the medperf platform
        Args:
            fedtrain_info (dict): federated training information
                expected keys:
                    name (str): federated training name
                    description (str): benchmark description
                    docs_url (str): benchmark documentation url
        """
        ui = config.ui
        submission = cls(fedtrain_info, no_cache)#, skip_data_preparation_step)

        with ui.interactive():
            # ui.text = "Getting additional information"
            # submission.get_extra_information()
            ui.print("> Completed benchmark registration information")
            ui.text = "Submitting Benchmark to MedPerf"
            updated_benchmark_body = submission.submit()
        ui.print("Uploaded")
        # TODO: I think this step can only be run once we've executed the training and have our results
        # submission.to_permanent_path(updated_benchmark_body)
        # submission.write(updated_benchmark_body)

    def __init__(
        self,
        fedtrain_info: dict,
        no_cache: bool = True,
        skip_data_preparation_step: bool = False,
    ):
        self.ui = config.ui
        self.ftr = FederatedTraining(**fedtrain_info)
        self.no_cache = no_cache
        # self.bmk.metadata["demo_dataset_already_prepared"] = skip_data_preparation_step
        config.tmp_paths.append(self.ftr.path)

    # def get_extra_information(self):
    #     """Retrieves information that must be populated automatically,
    #     like hash, generated uid and test results
    #     """
    #     bmk_demo_url = self.bmk.demo_dataset_tarball_url
    #     bmk_demo_hash = self.bmk.demo_dataset_tarball_hash
    #     try:
    #         _, demo_hash = resources.get_benchmark_demo_dataset(
    #             bmk_demo_url, bmk_demo_hash
    #         )
    #     except InvalidEntityError as e:
    #         raise InvalidEntityError(f"Demo dataset {bmk_demo_url}: {e}")
    #     self.bmk.demo_dataset_tarball_hash = demo_hash
    #     demo_uid, results = self.run_compatibility_test()
    #     self.bmk.demo_dataset_generated_uid = demo_uid
    #     self.bmk.metadata["results"] = results

    # def run_compatibility_test(self):
    #     """Runs a compatibility test to ensure elements are compatible,
    #     and to extract additional information required for submission
    #     """
    #     self.ui.print("Running compatibility test")
    #     self.bmk.write()
    #     data_uid, results = CompatibilityTestExecution.run(
    #         benchmark=self.bmk.generated_uid,
    #         no_cache=self.no_cache,
    #         skip_data_preparation_step=self.skip_data_preparation_step,
    #     )
    #
    #     return data_uid, results

    def submit(self):
        updated_body = self.ftr.upload()
        return updated_body

    def to_permanent_path(self, ftr_dict: dict):
        """Renames the temporary federated training submission to a permanent one

        Args:
            ftr_dict (dict): dictionary containing updated information of the submitted federated training
        """
        old_ftr_loc = self.ftr.path
        updated_ftr = FederatedTraining(**ftr_dict)
        new_ftr_loc = updated_ftr.path
        remove_path(new_ftr_loc)
        os.rename(old_ftr_loc, new_ftr_loc)

    def write(self, updated_body):
        ftr = FederatedTraining(**updated_body)
        ftr.write()
