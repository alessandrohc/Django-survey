import utils

import forms
from django.db import models

# width, dateFormat, renderer, hidden, align, type

class SimpleGrid(object):
    def to_grid(self, fields, rows, totalcount = None, json_add = {}, sort_field = 'id', sort_direction = 'DESC'):
        if not totalcount:
            totalcount = len(rows)
        jdict = {
            'success':True
           ,'metaData':{
                'root':'rows'
                ,'totalProperty':'totalCount'
                ,'successProperty':'success'
                ,'sortInfo':{
                   'field': sort_field
                   ,'direction': sort_direction
                }
                ,'fields':fields
                }
                ,'rows':rows
                ,'totalCount':totalcount
            }
        return utils.JSONserialise(jdict)


class VirtualField(object):
    def __init__(self, name):
        self.name = name

class ModelGrid(object):
    """From a `mapping` of extjs_names <=> django_field_names
    and `fields` order, give somes handfull methods to use with ExtJS
    """
    # Final mapping is mapping + dict(list_mapping)
    mapping = {}
    list_mapping = []

    # Fields describe default subset of fields from final mapping.
    fields = None
    #exclude = None


    model = None

    def __init__(self, model=None, exclude=None, mapping=None, fields=None):
        """ Initialize the grid with params given on ModelGrid Definition or
        __init__
        """
        # Model
        model = model or self.model
        if not model or not issubclass(model, models.Model):
            raise IndexError("Please give a Model")
        else:
            self.model = model      # the model to use as reference


        # Excludes and Includes
        #exclude = exclude or self.exclude

        self.columns = {}        # holds the fields

        model_fields = self.model._meta._fields()
        base_fields = model_fields

        # Model base fields and needed fields
        self.mfields = [ (f.name, f.name) for f in model_fields ]
        self.mapping = mapping or self.mapping or dict(self.mfields)

        # Assemble _mapping (final_mapping)
        from copy import copy
        self._mapping = copy(self.mapping)
        self._mapping.update((x, x) for x in self.list_mapping)

        self.fields = fields or self.fields or self._mapping.keys()

        # Get good field config for fields
        for field in base_fields:

            # XXX VirtualField  : wtf ?
            if field.__class__.__name__ == VirtualField:
                self.fields.append(self.Meta.fields_conf[field.name])
                continue
            fdict = {'name':field.name, 'header': field.name}

            if getattr(field, 'verbose_name', None):
                fdict['tooltip'] = u'%s' %  field.verbose_name

            if field.name == 'id':
                fdict['id']='id'
            if isinstance(field, models.DateTimeField):
                fdict['type'] = 'datetime'
                fdict['xtype'] = 'datecolumn'
                fdict['dateFormat'] = 'Y-m-d H:i:s'
                fdict['format'] = 'Y-m-d H:i:s'
            elif isinstance(field, models.DateField):
                fdict['type'] = 'date'
                fdict['xtype'] = 'datecolumn'
                fdict['dateFormat'] = 'Y-m-d'
                fdict['format'] = 'Y-m-d'
            elif isinstance(field, models.IntegerField):
                fdict['xtype'] = 'numbercolumn'
            elif isinstance(field, models.BooleanField):
                fdict['xtype'] = 'booleancolumn'
            elif isinstance(field, models.DecimalField):
                fdict['xtype'] = 'numbercolumn '
                fdict['renderer'] = 'function(v) {return (v.toFixed && v.toFixed(2) || 0);}'
            elif isinstance(field, models.ForeignKey):
                pass
            elif field.choices:
                #print 'FIELD CHOICES', field.choices
                a = {}
                for c in field.choices:
                    a[c[0]] = c[1]
                #fdict['renderer'] = 'function(v) {a = %s; return a[v] || "";}' % utils.JSONserialise(a)

            self.columns[field] = fdict

    def query_from_request(self, request, queryset, fields=None):
        """Wrap for query_from_request
        """
        fields = fields or self.fields
        dfields = {}
        if type(fields) == type([]):
            for x in fields:
                dfields[x] = self._mapping[x]
        else:
            dfields = fields
        return utils.query_from_request(request, queryset, dfields)

    def get_rows(self, queryset, start=0, limit=0, fields=None, *args, **kwargs):
        """
            return list from given queryset
            order the data based on given field list
            paging from start,limit
        """
        if not fields:
            fields = self.fields

        for f in fields:
            if f not in self._mapping.keys():
                raise AttributeError("No mapped field '%s'" % (f))

        if start or limit:
            count = queryset.count()
            if start > 0:
                queryset = queryset[int(start):]
            if limit > 0:
                queryset = queryset[:int(limit)]
        else:
            # if a queryset is an object list
            count = len(queryset)

        # Now update with specials methods
        data = []
        for obj in queryset:
            fk_obj = None
            old_fk_obj = None
            relation = None
            row = {}
            for field in fields:
                if "__" in self._mapping[field]:
                    # Handle ForeignKeys
                    from copy import copy
                    old_fk_obj = copy(fk_obj)
                    fk_obj = copy(obj)
                    for relation in self._mapping[field].split("__"):

                        # For FK with null=True, getattr will raise an AttributeError
                        try:
                            fk_obj = getattr(fk_obj, relation)
                        except AttributeError:
                            fk_obj = None
                            break
                    row[field] = fk_obj
                else:
                    row[field] = getattr(obj, self._mapping[field])

                # Get choices elements
                if row[field]:
                    _obj = old_fk_obj or obj
                    # Notes on old_fk_obj
                    #
                    # We take the old fk object because in 'blah__author__title':
                    # fk_obj is 'title'
                    # fk_old_object is author
                    # so we try "get_title_display" on "author" obj

                    _field = relation or self._mapping[field]
                    display = getattr(_obj, "get_%s_display" % _field, None)
                    if display:
                        row["%s_display" % field] = display()

            data.append(row)

        return data, count

    def get_rows_json(self, queryset, jsonerror=False, *args, **kwargs):
        """
            return json message from given queryset
            order the data based on given field list
            paging from start,limit
        """
        try :
            data, length = self.get_rows(queryset, *args, **kwargs)
        except Exception, e:
            # TODO : replace with loggin solution
            if not jsonerror:
                raise e
            result = {'success': False, "message": "Error : %s" % e}
        else:
            result = {"data" : data, "success": True, "results": length}
        from extjs.utils import ExtJSONEncoder as Extjson
        json_enc = Extjson(ensure_ascii=False)
        return json_enc.encode(result)

    def to_store(self, fields=None, url=None, *args, **kwargs):
        """Create DataStore for this grid
        """
        fields = fields or self.fields

        field_list = []
        rmap = dict((v, k) for k, v in self.mapping.items())
        for field in fields:
            for f in self.columns.values():
                if f['name'] == self._mapping[field]:
                    field_list.append(f)
        result = {'fields': field_list}
        if url:
            result['url'] = url
        return result


    def to_grid(self, queryset, start = 0, limit = 0, totalcount = None, json_add = {}, sort_field = 'id', sort_direction = 'DESC'):
        """ return the given queryset as an ExtJs grid config
        includes full metadata (columns, renderers, totalcount...)
        includes the rows data
        to be used in combination with Ext.ux.AutoGrid
        """
        if not totalcount:
            totalcount = queryset.count()

        #base_fields = self.get_fields(colModel)

        # todo : stupid ?
        id_field = base_fields[0]['name']

        jsondict = {
             'succes':True
            ,'metaData':{
                 'root':'rows'
                ,'totalProperty':'totalCount'
                ,'successProperty':'success'
                ,'idProperty':id_field
                ,'sortInfo':{
                   "field": sort_field
                   ,"direction": sort_direction
                }
                ,'fields':base_fields
            }
            #,'rows':self.get_rows(base_fields, queryset, start, limit)
            ,'totalCount':totalcount
        }
        if json_add:
            jsondict.update(json_add)

        #return utils.JSONserialise(jsondict)
