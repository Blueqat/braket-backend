# Braket-backend-blueqat (bqbraket)
Convert `blueqat.Circuit` to `braket.circuits.Circuit`.

## Install
`pip install braket-backend-blueqat`

# Usage
## Use as function
```py
from blueqat import Circuit
import bqbraket

braket_circuit = bqbraket.convert(Circuit().h[0].cx[0, 1])
```

## Use as backend
```py
from blueqat import Circuit
import bqbraket

# Register as backend
bqbraket.register_backend()

# Run with braketconverter backend
Circuit().h[0].cx[0, 1].run(backend="braketconverter")
