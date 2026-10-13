# -*- coding: utf-8 -*-
import maya.cmds as cmds
import maya.mel as mel


SDK_ATTRS = [
    {
        "longName": "Offset",
        "attrType": "float",
        "defaultValue": 0.0,
        "keyable": True,
    },
    {
        "longName": "WaveLength",
        "attrType": "float",
        "defaultValue": 1.0,
        "keyable": True,
    },
    {
        "longName": "WaveLength_Offset",
        "attrType": "float",
        "defaultValue": 0.01,
        "keyable": True,
    },
    {
        "longName": "Amplitude",
        "attrType": "float",
        "defaultValue": 0.0,
        "keyable": True,
    },
    {
        "longName": "Speed",
        "attrType": "float",
        "defaultValue": 1.0,
        "keyable": True,
    },
    {
        "longName": "Time_Scale",
        "attrType": "float",
        "defaultValue": 0.0,
        "minValue": 0.0,
        "maxValue": 1.0,
        "keyable": True,
    },
]


TARGET_ATTRS = [
    {
        "longName": "BlendExpression",
        "attrType": "bool",
        "defaultValue": 1,
        "keyable": True,
    },
]


def short_node_name(node):
    """
    Convert:
        |group1|pCube1
    into:
        pCube1
    """
    if not node:
        return ""

    return node.split("|")[-1]


def add_attr_if_missing(node, attr_data):
    """
    Add attr safely if missing.
    Also reset default value if attr already exists.
    """

    if not cmds.objExists(node):
        cmds.warning("Node does not exist: {}".format(node))
        return False

    long_name = attr_data.get("longName")
    attr_type = attr_data.get("attrType", "float")
    default_value = attr_data.get("defaultValue", 0.0)
    keyable = attr_data.get("keyable", True)
    has_min_value = "minValue" in attr_data
    has_max_value = "maxValue" in attr_data
    min_value = attr_data.get("minValue")
    max_value = attr_data.get("maxValue")

    if not long_name:
        cmds.warning("Missing longName in attr data.")
        return False

    if not cmds.attributeQuery(long_name, node=node, exists=True):
        kwargs = {"ln": long_name, "k": keyable}

        if attr_type == "string":
            kwargs["dt"] = "string"
        else:
            kwargs["at"] = attr_type
            kwargs["dv"] = default_value

        if has_min_value and attr_type in ["float", "double", "doubleLinear", "doubleAngle", "long", "short", "byte"]:
            kwargs["min"] = min_value

        if has_max_value and attr_type in ["float", "double", "doubleLinear", "doubleAngle", "long", "short", "byte"]:
            kwargs["max"] = max_value

        cmds.addAttr(node, **kwargs)

    plug = "{}.{}".format(node, long_name)

    if has_min_value and attr_type in ["float", "double", "doubleLinear", "doubleAngle", "long", "short", "byte"]:
        try:
            cmds.addAttr(plug, e=True, hasMinValue=True)
            cmds.addAttr(plug, e=True, min=min_value)
        except Exception:
            pass

    if has_max_value and attr_type in ["float", "double", "doubleLinear", "doubleAngle", "long", "short", "byte"]:
        try:
            cmds.addAttr(plug, e=True, hasMaxValue=True)
            cmds.addAttr(plug, e=True, max=max_value)
        except Exception:
            pass

    # Keep it keyable/channelBox visible
    try:
        cmds.setAttr(plug, e=True, k=keyable)
    except Exception:
        pass

    # Update default value, similar to your resetAttributeDefaultValue idea
    try:
        if attr_type != "string":
            cmds.addAttr(plug, e=True, dv=default_value)
    except Exception:
        pass

    return True


def ensure_sdk_attrs(main_controller, settings=None):
    """
    Add SDK expression attributes onto main controller.

    If settings is provided, only adds attrs where radio button is ON.
    """

    if not cmds.objExists(main_controller):
        cmds.warning("Main controller does not exist: {}".format(main_controller))
        return False

    attr_by_setting = {
        "offset": "Offset",
        "wavelength": "WaveLength",
        "wavelengthOffset": "WaveLength_Offset",
        "amplitude": "Amplitude",
        "speed": "Speed",
        "timeScale": "Time_Scale",
    }

    for attr_data in SDK_ATTRS:
        long_name = attr_data["longName"]

        # If settings exist, only add used attrs
        if settings:
            allow = False

            for setting_key, attr_name in attr_by_setting.items():
                if attr_name == long_name and settings.get(setting_key):
                    allow = True
                    break

            if not allow:
                continue

        add_attr_if_missing(main_controller, attr_data)

    return True


def ensure_target_attrs(target_nodes, add_blend_expression=True):
    """
    Add target attrs to generated expression targets.
    Example:
        BlendExpression
    """

    if not target_nodes:
        return False

    for node in target_nodes:
        if not cmds.objExists(node):
            cmds.warning("Target does not exist: {}".format(node))
            continue

        if add_blend_expression:
            for attr_data in TARGET_ATTRS:
                add_attr_if_missing(node, attr_data)
                

    return True


def clean_expression_name(name):
    """
    Maya expression node name safe cleanup.
    """

    if not name:
        name = "Trigonometric_Expression_EXP"

    name = name.strip()
    name = name.replace(" ", "_")
    name = name.replace(".", "_")
    name = name.replace("|", "_")
    name = name.replace(":", "_")

    return name


def create_or_update_expression(expression_name, expression_text):
    """
    Create new expression node or update existing one.
    """

    expression_name = clean_expression_name(expression_name)

    if not expression_text or not expression_text.strip():
        cmds.warning("Expression text is empty.")
        return None

    if cmds.objExists(expression_name):
        node_type = cmds.nodeType(expression_name)

        if node_type != "expression":
            cmds.warning(
                "Node already exists but is not an expression node: {}".format(expression_name)
            )
            return None

        cmds.expression(expression_name, e=True, s=expression_text)
        expr_node = expression_name

    else:
        expr_node = cmds.expression(
            name=expression_name,
            s=expression_text,
            ae=True,
            uc="all"
        )

    mel.eval('print("REMINDER : Expression node created/updated : {} \\n")'.format(expr_node))

    return expr_node


def create_trigonometric_expression(
    main_controller,
    target_nodes,
    expression_name,
    expression_text,
    settings=None,
    add_blend_expression=False,
):
    """
    Main function called by your Trigonometric_Expression UI Create button.

    Args:
        main_controller:
            The controller grabbed from your main UI.
            Example: pCube1

        target_nodes:
            Selected targets used to generate each expression line.
            Example: [pCube2, pCube3, pCube4]

        expression_name:
            Name from Script Node Name textField.

        expression_text:
            Code from CodeViewer.

        settings:
            Radio button dict from main UI.

        add_blend_expression:
            If True, add BlendExpression to target nodes.
    """

    if not main_controller:
        cmds.warning("Missing main controller.")
        return None

    main_controller = short_node_name(main_controller)

    if not cmds.objExists(main_controller):
        cmds.warning("Main controller does not exist: {}".format(main_controller))
        return None

    target_nodes = target_nodes or []
    target_nodes = [short_node_name(x) for x in target_nodes if x]

    ensure_sdk_attrs(main_controller, settings=settings)

    if add_blend_expression and target_nodes:
        ensure_target_attrs(target_nodes, add_blend_expression=True)

    expr_node = create_or_update_expression(
        expression_name=expression_name,
        expression_text=expression_text,
    )

    if not expr_node:
        cmds.warning("Failed to create expression node.")
        return None

    result = {
        "expressionNode": expr_node,
        "mainController": main_controller,
        "targetNodes": target_nodes,
        "expressionName": expression_name,
    }

    print(result)
    return result