import rtoml


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


class Tool(object):

    def dictToObj(self, dictObj):
        if not isinstance(dictObj, dict):
            return dictObj
        d = Dict()
        for k, v in dictObj.items():
            d[k] = self.dictToObj(v)
        return d


class ReadConfig(object):

    def parseFile(self, paths):
        data = rtoml.load(open(paths, 'r'))
        self.config = Tool().dictToObj(data)
        return self.config
