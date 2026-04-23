def _log_query(sql, params):
    try:
        return sql % params
    except Exception:
        return sql
    
def prepare_query(sql, params):
    sql = _log_query(sql, params)
    return sql