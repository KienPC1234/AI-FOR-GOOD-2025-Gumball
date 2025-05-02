# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.patient import PatientDetails # noqa
from app.models.scan import Scan # noqa
from app.models.token import DoctorConnectToken # noqa