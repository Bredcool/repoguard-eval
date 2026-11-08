"""API-specific exceptions."""


class ExperimentNotFoundError(Exception):
    pass


class ArtifactNotFoundError(Exception):
    pass


class ArtifactAccessError(Exception):
    pass


class ArtifactReadError(Exception):
    pass