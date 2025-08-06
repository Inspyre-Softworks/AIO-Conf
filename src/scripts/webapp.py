import streamlit as st
from typing import List, Optional, Union, Any
from dataclasses import dataclass, asdict
from aio_conf.core import OptionSpec, ConfigSpec
import ast
import json
from pprint import pformat
import re


TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list[str]": list[str],
}


def safe_literal(val: str):
    try:
        return ast.literal_eval(val)
    except Exception:
        return val


def sanitize_env_part(s: str) -> str:
    return s.strip().replace("-", "_").replace(" ", "_").upper()


def generate_cli_arg(name: str) -> str:
    return f"--{name.strip().lower().replace('_', '-').replace(' ', '-')}" if name else ""


def update_suggestions():
    prog_raw = st.session_state.prog_name.strip()

    if st.session_state.get("abbreviate_prog_name"):
        parts = re.split(r"[-_\s]+", prog_raw)
        prog_part = "".join(p[0].upper() for p in parts if p)
    else:
        prog_part = sanitize_env_part(prog_raw)

    name_raw = st.session_state.get("form_name", "").strip()
    name_part = sanitize_env_part(name_raw)

    if not st.session_state.get("form_env"):
        st.session_state["form_env"] = f"{prog_part}_{name_part}" if prog_part and name_part else ""

    if not st.session_state.get("form_cli"):
        long_flag = generate_cli_arg(name_raw)
        short_flag = f"-{name_raw[0].lower()}" if name_raw else ""
        st.session_state["form_cli"] = f"{long_flag}, {short_flag}" if short_flag else long_flag


@dataclass
class OptionDraft:
    name: str
    type: str
    default: str
    required: bool = False
    env: str = ""
    cli: str = ""
    description: str = ""

    def to_spec(self) -> OptionSpec:
        python_type = TYPE_MAP.get(self.type, str)
        default_val = safe_literal(self.default) if self.default else None
        cli_list = [arg.strip() for arg in self.cli.split(",")] if self.cli else None

        return OptionSpec(
            name=self.name,
            type=python_type,
            default=default_val,
            required=self.required,
            env=self.env or None,
            cli=cli_list,
            description=self.description or None,
        )


# --- Init Page ---
st.set_page_config(page_title="ConfigSpec Builder", page_icon="🛠️")
st.title("🛠️ AIO-Conf ConfigSpec Builder")

# --- State Init ---
st.session_state.setdefault("options", [])
st.session_state.setdefault("prog_name", "")
st.session_state.setdefault("last_add_success", False)
st.session_state.setdefault("editing_index", None)
st.session_state.setdefault("form_name", "")
st.session_state.setdefault("form_env", "")
st.session_state.setdefault("form_cli", "")
st.session_state.setdefault("abbreviate_prog_name", False)

# --- Program Name + Abbrev Checkbox ---
st.text_input("🔧 Program Name", value=st.session_state.prog_name, key="prog_name")
st.checkbox("🔤 Use Acronym for Program Name in Env Vars", key="abbreviate_prog_name")

# --- Sidebar Form ---
st.sidebar.header("➕ Add New Option")

with st.sidebar.form("new_option_form", clear_on_submit=True):
    name_input = st.text_input("Name", key="form_name")

    # Call this right after capturing the name
    if name_input:
        update_suggestions()

    type_ = st.selectbox("Type", list(TYPE_MAP.keys()))
    default = st.text_input("Default (Python literal)")
    required = st.checkbox("Required")

    st.text_input("Env Name", key="form_env")
    st.text_input("CLI Arg", key="form_cli")
    description = st.text_area("Description")

    submitted = st.form_submit_button("Add Option")
    if submitted:
        if not name_input.strip():
            st.sidebar.warning("⚠️ Option name cannot be empty.")
        else:
            st.session_state.options.append(
                OptionDraft(name_input, type_, default, required,
                            st.session_state["form_env"], st.session_state["form_cli"], description)
            )
            st.session_state.last_add_success = True
            st.rerun()


if st.session_state.last_add_success:
    st.sidebar.success("✅ Option added successfully!")
    st.session_state.last_add_success = False

# --- Edit Form ---
if st.session_state.editing_index is not None:
    idx = st.session_state.editing_index
    editing_opt = st.session_state.options[idx]

    st.subheader(f"✏️ Editing Option: `{editing_opt.name}`")
    with st.form("edit_option_form"):
        new_name = st.text_input("Name", value=editing_opt.name)
        new_type = st.selectbox("Type", list(TYPE_MAP.keys()), index=list(TYPE_MAP.keys()).index(editing_opt.type))
        new_default = st.text_input("Default", value=editing_opt.default)
        new_required = st.checkbox("Required", value=editing_opt.required)

        parts = re.split(r"[-_\s]+", st.session_state.prog_name.strip())
        prog_part = "".join(p[0].upper() for p in parts if p) if st.session_state.get("abbreviate_prog_name") else sanitize_env_part(st.session_state.prog_name)
        name_part = sanitize_env_part(new_name)
        suggested_env = f"{prog_part}_{name_part}" if prog_part and name_part else ""
        new_env = st.text_input("Env Name", value=editing_opt.env or suggested_env)

        cli_suggestion = generate_cli_arg(new_name)
        cli_field = editing_opt.cli or f"{cli_suggestion}, -{new_name[0].lower()}" if new_name else ""
        new_cli = st.text_input("CLI Arg", value=cli_field)

        new_description = st.text_area("Description", value=editing_opt.description)

        col1, col2 = st.columns(2)
        if col1.form_submit_button("💾 Save Changes"):
            st.session_state.options[idx] = OptionDraft(
                name=new_name,
                type=new_type,
                default=new_default,
                required=new_required,
                env=new_env,
                cli=new_cli,
                description=new_description
            )
            st.session_state.editing_index = None
            st.rerun()

        if col2.form_submit_button("❌ Cancel"):
            st.session_state.editing_index = None
            st.rerun()

    st.divider()

# --- Display Options ---
st.subheader("🧾 Current Options")
if not st.session_state.options:
    st.info("No options added yet. Use the sidebar to add one!")
else:
    for i, opt in enumerate(st.session_state.options):
        col1, col2, col3 = st.columns([4, 1, 1])
        col1.markdown(f"**{opt.name}** `{opt.type}` — _default:_ `{opt.default}`")
        if col2.button("✏️ Edit", key=f"edit_{i}"):
            st.session_state.editing_index = i
            st.rerun()
        if col3.button("❌ Remove", key=f"remove_{i}"):
            st.session_state.options.pop(i)
            st.rerun()

    if st.button("🗑️ Clear All Options"):
        st.session_state.options.clear()
        st.rerun()

# --- Generate & Download ---
st.divider()
if st.button("🚀 Generate ConfigSpec"):
    try:
        specs = [o.to_spec() for o in st.session_state.options]
        config = ConfigSpec(specs)
        st.success("🎉 ConfigSpec generated successfully!")
        st.code(pformat(asdict(config)), language="python")

        py_code = (
            "from aio_conf.core import OptionSpec, ConfigSpec\n\n"
            "options = [\n"
            + ",\n".join(
                f"    OptionSpec(name={repr(o.name)}, type={TYPE_MAP[o.type].__name__}, default={repr(safe_literal(o.default)) if o.default else None}, "
                f"required={o.required}, env={repr(o.env)}, "
                f"cli={repr([arg.strip() for arg in o.cli.split(',')] if isinstance(o.cli, str) else o.cli)}, "
                f"description={repr(o.description)})"
                for o in st.session_state.options
            )
            + "\n]\n\nconfig = ConfigSpec(options)"
        )

        st.download_button("📥 Download ConfigSpec as Python", py_code, "configspec.py", "text/x-python")
        st.download_button("📄 Download as JSON", json.dumps([asdict(o) for o in st.session_state.options], indent=2), "configspec.json", "application/json")

    except Exception as e:
        st.error(f"❌ Failed to generate ConfigSpec: {e}")
