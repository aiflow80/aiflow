import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiflow import mui

def card_component():
        with mui.Grid(item=True, xs=12):
            with mui.Grid(container=True, spacing=2):
                for i in range(2):
                    with mui.Grid(item=True, lg=4, md=6, sm=6, xs=12):
                        with mui.Card(
                            sx={
                                "display": "flex",
                                "flexDirection": "column",
                                "borderRadius": 3,
                                "overflow": "hidden",
                            },
                            elevation=1
                        ):
                            mui.CardHeader(
                                title="Shrimp and Chorizo Paella",
                                subheader="September 14, 2016",
                                avatar=mui.Avatar("R", sx={"bgcolor": "red"}),
                                action=mui.IconButton(mui.icon.MoreVert),
                            )

                            mui.CardMedia(
                                component="img",
                                height=294,
                                image="https://mui.com/static/images/cards/paella.jpg",
                                alt="Paella dish",
                            )
                            
                            with mui.CardContent(sx={"flex": 1}):
                                mui.Typography(
                                    "This impressive paella is a perfect party dish and a fun meal to cook together "
                                    "with your guests. Add 1 cup of frozen peas along with the mussels, if you like."
                                )

if __name__ == "__main__":
    card_component()