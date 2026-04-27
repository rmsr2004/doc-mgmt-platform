import app.components.dal.users as users
from app.shared.result.Result import Error, Result

def get_all_users() -> Result:
    users_list = users.get_all_users()
    
    # error from database
    if type(users_list) is Error:
        return Result.fail(users_list)

    return Result.ok(users_list)

def update_user_status(user_id) -> Result:
    result = users.update_user_status(user_id)
    
    # error from database
    if type(result) is Error:
        return Result.fail(result)
    
    return Result.ok(None)