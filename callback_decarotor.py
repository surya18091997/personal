def callback(callback_func, *cargs, **ckwargs):
    def dec1(func):
        def modded_deco(*cargss, **ckwargss):
            if not callable(callback_func):
                return func(*cargss, **ckwargss)
            initial_func_return_val = func(*cargss, **ckwargss)
            if initial_func_return_val:
                return callback_func(*initial_func_return_val, *cargs, **ckwargs)
            return callback_func(*cargs, **ckwargs)

        return modded_deco
    return dec1


def q(w1, w2):
    print("qqww", w1, w2)


@callback(q)
def q1(w):
    return w, w + 1


q1(1)
