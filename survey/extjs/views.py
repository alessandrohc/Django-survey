from extjs.grids import ModelGrid
from extjs.utils import JsonResponse

def query_to_grid(request, modelgrid, queryset, *args, **kwargs):
    """With a model grid and a query set, get extjs store
    """
    #if not isinstance(modelgrid, ModelGrid):
    #    raise Exception("")
    result = modelgrid().get_rows_json(queryset, *args, **kwargs)
    return JsonResponse(result)
