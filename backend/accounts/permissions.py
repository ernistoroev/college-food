from rest_framework.permissions import SAFE_METHODS, BasePermission

# Canteen staff are the members of this Django group (created by migration accounts/0002).
STAFF_GROUP = 'Сотрудники столовой'


def is_canteen_staff(user):
    """A superuser counts as staff too, so the project owner can manage everything."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=STAFF_GROUP).exists()


def get_role(user):
    """The role the frontend uses to choose the interface: 'staff' or 'student'."""
    return 'staff' if is_canteen_staff(user) else 'student'


class IsCanteenStaff(BasePermission):
    """Only canteen staff."""

    message = 'Это действие доступно только сотрудникам столовой.'

    def has_permission(self, request, view):
        return is_canteen_staff(request.user)


class IsStaffOrReadOnly(BasePermission):
    """Everyone can read (GET); only canteen staff can create, change and delete."""

    message = 'Изменять это может только сотрудник столовой.'

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_canteen_staff(request.user)


class IsStudent(BasePermission):
    """Only a logged-in student (not staff)."""

    message = 'Это действие доступно только студентам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and not is_canteen_staff(request.user)


class IsStudentOrReadOnly(BasePermission):
    """Everyone can read; only a logged-in student (not staff) can write."""

    message = 'Это действие доступно только студентам.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and not is_canteen_staff(request.user)
