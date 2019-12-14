def safeGet(data, path, default=None):
    pathParts = path.split('.')

    dataPart = data
    
    try:
        for part in pathParts:
            if part.startswith('['):
                dataPart = dataPart[int(part[1:-1])]
            else:
                dataPart = dataPart[part]

        return dataPart
    except:
        return default

def get(data, path):
    pathParts = path.split('.')

    dataPart = data

    for part in pathParts:
        if part.startswith('['):
            dataPart = dataPart[int(part[1:-1])]
        else:
            dataPart = dataPart[part]

    return dataPart