import os
import uuid

from medperf.exceptions import MedperfException
import yaml
import logging
from typing import List, Optional, Union
from pydantic import HttpUrl, Field

import medperf.config as config
from medperf.entities.interface import Entity, Uploadable
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError
from medperf.entities.schemas import MedperfSchema, ApprovableSchema, DeployableSchema
from medperf.account_management import get_medperf_user_data


class FederatedTraining(Entity, Uploadable, MedperfSchema, ApprovableSchema, DeployableSchema):
    """
    Class representing a federated training

    A federated training is associates a federated model and client
    allowing the training of the model on live data from multiple clients.
    After the training, the model weights can be retrieved by the owner
    of the federated model.
    """

    description: Optional[str] = Field(None, max_length=20)
    docs_url: Optional[HttpUrl]
    # demo_dataset_tarball_url: str
    # demo_dataset_tarball_hash: Optional[str]
    # demo_dataset_generated_uid: Optional[str]
    # data_preparation_mlcube: int
    # reference_model_mlcube: int
    # data_evaluator_mlcube: int
    metadata: dict = {}
    user_metadata: dict = {}
    is_active: bool = True

    def __init__(self, *args, **kwargs):
        """Creates a new benchmark instance

        Args:
            bmk_desc (Union[dict, BenchmarkModel]): Benchmark instance description
        """
        super().__init__(*args, **kwargs)

        # self.generated_uid = f"p{self.data_preparation_mlcube}m{self.reference_model_mlcube}e{self.data_evaluator_mlcube}"
        self.generated_uid = "foo_bar"#uuid.uuid4().hex
        path = config.federated_training_folder
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)
        self.path = path

    @classmethod
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["FederatedTraining"]:
        """Gets and creates instances of all retrievable federated_trainings

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[FederatedTraining]: a list of Benchmark instances.
        """
        logging.info("Retrieving all federated trainings")
        federated_trainings = []

        if not local_only:
            federated_trainings = cls.__remote_all(filters=filters)

        remote_uids = set([ftr.id for ftr in federated_trainings])

        local_federated_trainings = cls.__local_all()

        federated_trainings += [ftr for ftr in local_federated_trainings if ftr.id not in remote_uids]

        return federated_trainings

    @classmethod
    def __remote_all(cls, filters: dict) -> List["FederatedTraining"]:
        federated_trainings = []
        try:
            comms_fn = cls.__remote_prefilter(filters)
            ftrs_meta = comms_fn()
            federated_trainings = [cls(**meta) for meta in ftrs_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all federated_trainings from the server"
            logging.warning(msg)

        return federated_trainings

    @classmethod
    def __remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_federated_trainings
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_federated_trainings
        return comms_fn

    @classmethod
    def __local_all(cls) -> List["FederatedTraining"]:
        federated_trainings = []
        ftr_storage = config.federated_training_folder
        try:
            uids = next(os.walk(ftr_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over federated trainings directory"
            logging.warning(msg)
            raise MedperfException(msg)

        for uid in uids:
            meta = cls.__get_local_dict(uid)
            fedtrain = cls(**meta)
            federated_trainings.append(fedtrain)

        return federated_trainings

    @classmethod
    def get(
        cls, fedtrain_uid: Union[str, int], local_only: bool = False
    ) -> "FederatedTraining":
        """Retrieves and creates a Federated Training instance from the server.
        If the federated training already exists in the platform then retrieve that
        version.

        Args:
            fedtrain_uid (str): UID of the benchmark.
            comms (Comms): Instance of a communication interface.

        Returns:
            FederatedTraining: a Benchmark instance with the retrieved data.
        """

        if not str(fedtrain_uid).isdigit() or local_only:
            return cls.__local_get(fedtrain_uid)

        try:
            return cls.__remote_get(fedtrain_uid)
        except CommunicationRetrievalError:
            logging.warning(f"Getting Federated Training {fedtrain_uid} from comms failed")
            logging.info(f"Looking for Federated Training {fedtrain_uid} locally")
            return cls.__local_get(fedtrain_uid)

    @classmethod
    def __remote_get(cls, fedtrain_uid: int) -> "FederatedTraining":
        """Retrieves and creates a Federated Training instance from the comms instance.
        If the federated training is present in the user's machine then it retrieves it from there.

        Args:
            fedtrain_uid (str): server UID of the dataset

        Returns:
            FederatedTraining: Specified federated training instance
        """
        logging.debug(f"Retrieving federated training {fedtrain_uid} remotely")
        fedtrain_dict = config.comms.get_benchmark(fedtrain_uid)
        fedtrain = cls(**fedtrain_dict)
        fedtrain.write()
        return fedtrain

    @classmethod
    def __local_get(cls, fedtrain_uid: Union[str, int]) -> "FederatedTraining":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            dset_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving federated training {fedtrain_uid} locally")
        fedtrain_dict = cls.__get_local_dict(fedtrain_uid)
        fedtrain = cls(**fedtrain_dict)
        return fedtrain

    @classmethod
    def __get_local_dict(cls, fedtrain_uid) -> dict:
        """Retrieves a local federated training information

        Args:
            fedtrain_uid (str): uid of the local federated training

        Returns:
            dict: information of the federated training
        """
        logging.info(f"Retrieving federated training {fedtrain_uid} from local storage")
        storage = config.federated_training_folder
        ftr_storage = os.path.join(storage, str(fedtrain_uid))
        ftr_file = os.path.join(ftr_storage, config.fedtrain_filename)
        if not os.path.exists(ftr_file):
            raise InvalidArgumentError("No federated training with the given uid could be found")
        with open(ftr_file, "r") as f:
            data = yaml.safe_load(f)

        return data

    # @classmethod
    # def get_models_uids(cls, benchmark_uid: int) -> List[int]:
    #     """Retrieves the list of models associated to the benchmark
    #
    #     Args:
    #         benchmark_uid (int): UID of the benchmark.
    #         comms (Comms): Instance of the communications interface.
    #
    #     Returns:
    #         List[int]: List of mlcube uids
    #     """
    #     associations = config.comms.get_benchmark_model_associations(benchmark_uid)
    #     models_uids = [
    #         assoc["model_mlcube"]
    #         for assoc in associations
    #         if assoc["approval_status"] == "APPROVED"
    #     ]
    #     return models_uids
    #
    def todict(self) -> dict:
        """Dictionary representation of the benchmark instance

        Returns:
        dict: Dictionary containing benchmark information
        """
        return self.extended_dict()

    def write(self) -> str:
        """Writes the federated training into disk

        Args:
            filename (str, optional): name of the file. Defaults to config.fedtrain_filename.

        Returns:
            str: path to the created federated training file
        """
        data = self.todict()
        ftr_file = os.path.join(self.path, config.fedtrain_filename)
        # TODO: remove debug comments
        print(f"ftr_file: {ftr_file}")
        if not os.path.exists(ftr_file):
            print(f"making dir: {self.path}")
            os.makedirs(self.path, exist_ok=True)
        with open(ftr_file, "w") as f:
            print(f"dumping yaml: {f.name}")
            yaml.dump(data, f)
        return ftr_file

    def upload(self):
        """Uploads a federated training to the server

        Args:
            comms (Comms): communications entity to submit through
        """
        if self.for_test:
            raise InvalidArgumentError("Cannot upload test federated trainings.")
        body = self.todict()
        updated_body = config.comms.upload_federated_training(body)
        return updated_body

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            # "Data Preparation MLCube": int(self.data_preparation_mlcube),
            # "Reference Model MLCube": int(self.reference_model_mlcube),
            # "Data Evaluator MLCube": int(self.data_evaluator_mlcube),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
