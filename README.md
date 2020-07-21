# USD Prim's Display State layer

This is a small generic model to manages the display state of the prims in a USD scene inside a client application. 
It takes the UsdStage as __init__'s argument and crates a SdfLayer to store all the Display overrides. 
Since the Load state of a prim is not written as an USD Attribute, the model performs the task of saving and applying the
loading state on each stored prim. 

To turn the effects of the layer on/off, use the Model's setMuted method, NOT the SdfLayer.SetMuted.

This model controls the following display options:

- Payloads' loading state
- Prim's activation
- Drawing mode (when supported by the client)
- Purposes
- Purposes Swap - Turns proxy renderable and deactivates High Detail model. 

For examples of use, please check **./tests/tests_prims_display_manager.py**