import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiflow import mui
from aiflow.events import events_store  # Direct import of the events dictionary

skills_options = [
    "Python", "JavaScript", "React", "Java", "C++", "SQL", 
    "Data Analysis", "Machine Learning", "Cloud Computing",
    "DevOps", "Agile", "Project Management"
]

# Card container for the form
with mui.Card(variant="outlined", sx={"padding": "16px", "maxWidth": "100%", "margin": "0 auto"}):
    
    # Form title using Typography
    mui.Typography("User Registration Form", variant="h4", gutterBottom=True)

    # Alert for instructions
    mui.Alert("Please fill out the form carefully and review the details before submitting.", 
                severity="info", variant="outlined", sx={"marginBottom": "20px"})

    # Profile Avatar
    mui.Avatar("A", sx={"width": 80, "height": 80, "marginBottom": "20px"})

    # Input fields for registration
    mui.TextField(id="first-name", label="First Name", variant="outlined", fullWidth=True, sx={"marginBottom": "10px"})
    mui.TextField(id="last-name", label="Last Name", variant="outlined", fullWidth=True, sx={"marginBottom": "10px"})

    # Role selection using Chips
    mui.Typography("Select Role:", id="role-label", variant="subtitle1", sx={"marginBottom": "10px"})
    mui.Chip(id="role-user", label="User", variant="outlined", color="primary", sx={"marginRight": "10px"})
    mui.Chip(id="role-admin", label="Admin", variant="outlined", color="secondary", sx={"marginRight": "10px"})
    mui.Chip(id="role-moderator", label="Moderator", variant="outlined", color="success", sx={"marginRight": "10px"})

    # Additional fields using Paper for organization
    with mui.Paper(variant="outlined", sx={"padding": "10px", "marginTop": "20px", "marginBottom": "10px"}):
        mui.Typography("Additional Information", id="additional-info-title", variant="h6", gutterBottom=True)
        mui.TextField(id="company", label="Company", variant="outlined", fullWidth=True, sx={"marginBottom": "10px"})
        mui.TextField(id="position", label="Position", variant="outlined", fullWidth=True, sx={"marginBottom": "10px"})
                    
        # Fix Autocomplete component
        mui.Autocomplete(
            id="skills-autocomplete",
            multiple=True,
            options=skills_options,
            defaultValue=[],
            renderInput="(params) => createElement(TextField, {...params, label: 'Skills', variant: 'outlined', fullWidth: true})",
            sx={"marginBottom": "10px"}
        )

    # Experience level using Slider
    mui.Typography("Years of Experience:", variant="subtitle1")
    mui.Slider(
        id="experience-slider",
        defaultValue=3,
        step=1,
        marks=True,
        min=0,
        max=10,
        valueLabelDisplay="auto",
        sx={"marginBottom": "20px"}
    )

    mui.Divider(id="gender-divider", sx={"marginY": "20px"})
    mui.Typography("Gender:", variant="subtitle1", sx={"marginBottom": "10px"})

    with mui.RadioGroup(defaultValue="female", id="gender", sx={"marginBottom": "15px"}):
        mui.FormControlLabel(value="female", control=mui.Radio(), label="Female")
        mui.FormControlLabel(value="male", control=mui.Radio(), label="Male")
        mui.FormControlLabel(value="other", control=mui.Radio(), label="Other")

        # Notification preferences using Checkboxes
        mui.Divider(sx={"marginY": "20px"})
        mui.Typography("Notification Preferences:", variant="subtitle1", sx={"marginBottom": "10px"})
        mui.FormControlLabel(id="notify-email", control=mui.Checkbox(defaultChecked=True), label="Email notifications")
        mui.FormControlLabel(id="notify-sms", control=mui.Checkbox(), label="SMS notifications")
        mui.FormControlLabel(id="notify-push", control=mui.Checkbox(), label="Push notifications")

        # Satisfaction rating
        mui.Divider(sx={"marginY": "20px"})
        mui.Typography("Rate your experience:", variant="subtitle1")
        mui.Rating(id="satisfaction-rating", defaultValue=3, precision=0.5, sx={"marginBottom": "20px"})

        # Terms and conditions toggle
        mui.Divider(sx={"marginY": "20px"})
        mui.FormControlLabel(
            id="terms-switch",
            control=mui.Switch(required=True),
            label="I accept the terms and conditions",
            sx={"marginBottom": "20px"}
        )

        # # Select Box
        # mui.Typography("Select Department:", variant="subtitle1", sx={"marginTop": "20px", "marginBottom": "10px"})
        # with mui.Select(id="department-select", variant="outlined", fullWidth=True, sx={"marginBottom": "10px"}) as department_select:
        #     for index, department in enumerate(["HR", "Engineering", "Marketing", "Sales"]):
        #         mui.MenuItem(
        #             department, 
        #             value=department, 
        #             option=f"option-{index}",
        #             id=f"dept-{department.lower()}",
        #             sx={
        #                 "padding": "12px 16px",
        #                 "minHeight": "42px",
        #                 "&:hover": {
        #                     "backgroundColor": "rgba(0, 0, 0, 0.04)"
        #                 }
        #             }
        #         )

        # Debugging section to display events
        if events_store.get('events'):
            with mui.Box(sx={"marginTop": "40px", "padding": "16px",  "borderRadius": "4px"}):
                mui.Typography("Event Store Contents:", variant="h6", gutterBottom=True)
                mui.Typography(str(events_store), variant="body2", sx={"whiteSpace": "pre-wrap", "fontFamily": "monospace"})


    mui.Button("Submit", id="submit-button", type="submit", variant="contained", color="primary", sx={"marginTop": "20px", "marginBottom": "10px", "float": "right"})
        
