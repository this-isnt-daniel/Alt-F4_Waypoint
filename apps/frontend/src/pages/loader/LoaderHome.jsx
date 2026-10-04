import React, { useState, useMemo, useRef, useEffect } from 'react';
import LoaderMap from './LoaderMap';

const MOCK_VEHICLES = [
  {
    "id": "VEH011",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Gampaha Fresh",
    "stops": 3,
    "status": "En Route",
    "color": "blue",
    "desc": "Expected Depot Return: 08:22 AM",
    "location": {
      "lat": 7.0873,
      "lng": 79.9995
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.0873,
        "lng": 79.9995
      }
    ]
  },
  {
    "id": "VEH009",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Gampaha Fresh",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "eta": "ETA: 08:45 AM (In 15 mins)",
    "action": "Pre-stage next trip cargo",
    "location": {
      "lat": 7.01,
      "lng": 79.93
    },
    "routeCoords": [
      {
        "lat": 7.0873,
        "lng": 79.9995
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH019",
    "depot": "peliyagoda",
    "type": "Van · Ambient",
    "route": "Colombo Central Style",
    "stops": 4,
    "status": "Delayed",
    "color": "red",
    "desc": "Adjusted return: 10:42 AM (+22m late)",
    "isRedDesc": true,
    "location": {
      "lat": 6.9271,
      "lng": 79.8612
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9271,
        "lng": 79.8612
      }
    ]
  },
  {
    "id": "VEH041",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Liberty Plaza Style",
    "stops": null,
    "status": "Dispatched",
    "color": "brand",
    "desc": "Released 03:28 AM · Driver: S. Perera",
    "location": {
      "lat": 6.9099,
      "lng": 79.8519
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9099,
        "lng": 79.8519
      }
    ]
  },
  {
    "id": "VEH014",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Gampaha Fresh North",
    "stops": 5,
    "status": "En Route",
    "color": "blue",
    "desc": "Expected Depot Return: 09:15 AM",
    "location": {
      "lat": 7.2008,
      "lng": 79.8737
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.2008,
        "lng": 79.8737
      }
    ]
  },
  {
    "id": "VEH-K01",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Peradeniya Route",
    "stops": 4,
    "status": "En Route",
    "color": "blue",
    "desc": "Expected Depot Return: 07:15 AM",
    "location": {
      "lat": 7.2687,
      "lng": 80.5975
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.2687,
        "lng": 80.5975
      }
    ]
  },
  {
    "id": "VEH-K02",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Katugastota Fresh",
    "stops": 6,
    "status": "Returning",
    "color": "orange",
    "eta": "ETA: 08:10 AM (In 20 mins)",
    "action": "Pre-stage next trip cargo",
    "location": {
      "lat": 7.3,
      "lng": 80.63
    },
    "routeCoords": [
      {
        "lat": 7.3235,
        "lng": 80.6212
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-K05",
    "depot": "kandy",
    "type": "Van · Ambient",
    "route": "Kandy Town Style",
    "stops": null,
    "status": "Dispatched",
    "color": "brand",
    "desc": "Released 04:15 AM · Driver: K. Bandara",
    "location": {
      "lat": 7.295,
      "lng": 80.635
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.295,
        "lng": 80.635
      }
    ]
  },
  {
    "id": "VEH-P101",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P1",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.9352180258874405,
      "lng": 80.0183706596194
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9352180258874405,
        "lng": 80.0183706596194
      }
    ]
  },
  {
    "id": "VEH-P201",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P1 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.003562625525806,
      "lng": 80.0245042800858
    },
    "routeCoords": [
      {
        "lat": 7.003562625525806,
        "lng": 80.0245042800858
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K101",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K1",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.245456460218662,
      "lng": 80.62481645920889
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.245456460218662,
        "lng": 80.62481645920889
      }
    ]
  },
  {
    "id": "VEH-K201",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K1 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.297147629364571,
      "lng": 80.65325516690191
    },
    "routeCoords": [
      {
        "lat": 7.297147629364571,
        "lng": 80.65325516690191
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P102",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P2",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.937245198202811,
      "lng": 79.89839546670233
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.937245198202811,
        "lng": 79.89839546670233
      }
    ]
  },
  {
    "id": "VEH-P202",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P2 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.055994669905862,
      "lng": 79.95327576989816
    },
    "routeCoords": [
      {
        "lat": 7.055994669905862,
        "lng": 79.95327576989816
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K102",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K2",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.299340019836844,
      "lng": 80.67901729347757
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.299340019836844,
        "lng": 80.67901729347757
      }
    ]
  },
  {
    "id": "VEH-K202",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K2 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.302896318875141,
      "lng": 80.6586580005471
    },
    "routeCoords": [
      {
        "lat": 7.302896318875141,
        "lng": 80.6586580005471
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P103",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P3",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.9604629071656205,
      "lng": 79.90049853984408
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9604629071656205,
        "lng": 79.90049853984408
      }
    ]
  },
  {
    "id": "VEH-P203",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P3 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.042500846967318,
      "lng": 79.98187491072643
    },
    "routeCoords": [
      {
        "lat": 7.042500846967318,
        "lng": 79.98187491072643
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K103",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K3",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.322666972586512,
      "lng": 80.59355722995303
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.322666972586512,
        "lng": 80.59355722995303
      }
    ]
  },
  {
    "id": "VEH-K203",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K3 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.250466676591854,
      "lng": 80.64848931483041
    },
    "routeCoords": [
      {
        "lat": 7.250466676591854,
        "lng": 80.64848931483041
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P104",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P4",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.936490345786265,
      "lng": 79.93143274067535
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.936490345786265,
        "lng": 79.93143274067535
      }
    ]
  },
  {
    "id": "VEH-P204",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P4 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.016220157388682,
      "lng": 79.89845603707707
    },
    "routeCoords": [
      {
        "lat": 7.016220157388682,
        "lng": 79.89845603707707
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K104",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K4",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.280729873960024,
      "lng": 80.60966339281426
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.280729873960024,
        "lng": 80.60966339281426
      }
    ]
  },
  {
    "id": "VEH-K204",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K4 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.247275019387744,
      "lng": 80.65592965860448
    },
    "routeCoords": [
      {
        "lat": 7.247275019387744,
        "lng": 80.65592965860448
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P105",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P5",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.009748383577316,
      "lng": 79.89410122332114
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.009748383577316,
        "lng": 79.89410122332114
      }
    ]
  },
  {
    "id": "VEH-P205",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P5 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.9807897676782815,
      "lng": 79.9242127778645
    },
    "routeCoords": [
      {
        "lat": 6.9807897676782815,
        "lng": 79.9242127778645
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K105",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K5",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.242105937222938,
      "lng": 80.66576165535785
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.242105937222938,
        "lng": 80.66576165535785
      }
    ]
  },
  {
    "id": "VEH-K205",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K5 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.330659461782987,
      "lng": 80.64631406637866
    },
    "routeCoords": [
      {
        "lat": 7.330659461782987,
        "lng": 80.64631406637866
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P106",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P6",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.93620359570278,
      "lng": 79.96102060318134
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.93620359570278,
        "lng": 79.96102060318134
      }
    ]
  },
  {
    "id": "VEH-P206",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P6 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.043810908446144,
      "lng": 79.90183874244524
    },
    "routeCoords": [
      {
        "lat": 7.043810908446144,
        "lng": 79.90183874244524
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K106",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K6",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.308539011351809,
      "lng": 80.6375827779564
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.308539011351809,
        "lng": 80.6375827779564
      }
    ]
  },
  {
    "id": "VEH-K206",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K6 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.278890873454071,
      "lng": 80.58683236582779
    },
    "routeCoords": [
      {
        "lat": 7.278890873454071,
        "lng": 80.58683236582779
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P107",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P7",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.944594081282661,
      "lng": 79.92696276134458
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.944594081282661,
        "lng": 79.92696276134458
      }
    ]
  },
  {
    "id": "VEH-P207",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P7 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.969269470674926,
      "lng": 79.92752634526518
    },
    "routeCoords": [
      {
        "lat": 6.969269470674926,
        "lng": 79.92752634526518
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K107",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K7",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.306351382625994,
      "lng": 80.67893953301935
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.306351382625994,
        "lng": 80.67893953301935
      }
    ]
  },
  {
    "id": "VEH-K207",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K7 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.297075875297991,
      "lng": 80.63783530961706
    },
    "routeCoords": [
      {
        "lat": 7.297075875297991,
        "lng": 80.63783530961706
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P108",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P8",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.043672529009982,
      "lng": 79.9256741144788
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.043672529009982,
        "lng": 79.9256741144788
      }
    ]
  },
  {
    "id": "VEH-P208",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P8 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.991521951362268,
      "lng": 79.92865334088737
    },
    "routeCoords": [
      {
        "lat": 6.991521951362268,
        "lng": 79.92865334088737
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K108",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K8",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.299452521711508,
      "lng": 80.60664639215773
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.299452521711508,
        "lng": 80.60664639215773
      }
    ]
  },
  {
    "id": "VEH-K208",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K8 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.246374517491141,
      "lng": 80.62133437663117
    },
    "routeCoords": [
      {
        "lat": 7.246374517491141,
        "lng": 80.62133437663117
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P109",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P9",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.9974279701067195,
      "lng": 79.95256406818595
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9974279701067195,
        "lng": 79.95256406818595
      }
    ]
  },
  {
    "id": "VEH-P209",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P9 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.91768057394362,
      "lng": 79.92903249173564
    },
    "routeCoords": [
      {
        "lat": 6.91768057394362,
        "lng": 79.92903249173564
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K109",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K9",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.292740317416343,
      "lng": 80.62360759492337
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.292740317416343,
        "lng": 80.62360759492337
      }
    ]
  },
  {
    "id": "VEH-K209",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K9 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.304822899415852,
      "lng": 80.6412857677111
    },
    "routeCoords": [
      {
        "lat": 7.304822899415852,
        "lng": 80.6412857677111
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P110",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P10",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.00635470320122,
      "lng": 79.92801350448596
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.00635470320122,
        "lng": 79.92801350448596
      }
    ]
  },
  {
    "id": "VEH-P210",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P10 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.065293537165269,
      "lng": 79.91305586635411
    },
    "routeCoords": [
      {
        "lat": 7.065293537165269,
        "lng": 79.91305586635411
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K110",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K10",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.299828055020953,
      "lng": 80.61493464494691
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.299828055020953,
        "lng": 80.61493464494691
      }
    ]
  },
  {
    "id": "VEH-K210",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K10 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.297973396052944,
      "lng": 80.66819869180416
    },
    "routeCoords": [
      {
        "lat": 7.297973396052944,
        "lng": 80.66819869180416
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P111",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P11",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.9991151187774205,
      "lng": 79.90154080234771
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.9991151187774205,
        "lng": 79.90154080234771
      }
    ]
  },
  {
    "id": "VEH-P211",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P11 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.921855730993566,
      "lng": 79.93154896388128
    },
    "routeCoords": [
      {
        "lat": 6.921855730993566,
        "lng": 79.93154896388128
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K111",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K11",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.327987508192923,
      "lng": 80.60518053334967
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.327987508192923,
        "lng": 80.60518053334967
      }
    ]
  },
  {
    "id": "VEH-K211",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K11 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.283593635281715,
      "lng": 80.66906375176244
    },
    "routeCoords": [
      {
        "lat": 7.283593635281715,
        "lng": 80.66906375176244
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P112",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P12",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.042961934464916,
      "lng": 79.9222835730057
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.042961934464916,
        "lng": 79.9222835730057
      }
    ]
  },
  {
    "id": "VEH-P212",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P12 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.04314761220062,
      "lng": 79.89416295858345
    },
    "routeCoords": [
      {
        "lat": 7.04314761220062,
        "lng": 79.89416295858345
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K112",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K12",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.276907520530264,
      "lng": 80.6594310693027
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.276907520530264,
        "lng": 80.6594310693027
      }
    ]
  },
  {
    "id": "VEH-K212",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K12 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.2735280708637395,
      "lng": 80.65665378667006
    },
    "routeCoords": [
      {
        "lat": 7.2735280708637395,
        "lng": 80.65665378667006
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P113",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P13",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.925247140191991,
      "lng": 79.90336923004988
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.925247140191991,
        "lng": 79.90336923004988
      }
    ]
  },
  {
    "id": "VEH-P213",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P13 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.017743343535325,
      "lng": 80.02713166359314
    },
    "routeCoords": [
      {
        "lat": 7.017743343535325,
        "lng": 80.02713166359314
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K113",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K13",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.309630724912754,
      "lng": 80.64339232171727
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.309630724912754,
        "lng": 80.64339232171727
      }
    ]
  },
  {
    "id": "VEH-K213",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K13 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.2766194975651475,
      "lng": 80.67330278190649
    },
    "routeCoords": [
      {
        "lat": 7.2766194975651475,
        "lng": 80.67330278190649
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P114",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P14",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.94397964403702,
      "lng": 79.99472533219327
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.94397964403702,
        "lng": 79.99472533219327
      }
    ]
  },
  {
    "id": "VEH-P214",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P14 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.9418125859753586,
      "lng": 79.98038367158306
    },
    "routeCoords": [
      {
        "lat": 6.9418125859753586,
        "lng": 79.98038367158306
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K114",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K14",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.311913383994979,
      "lng": 80.66236303736004
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.311913383994979,
        "lng": 80.66236303736004
      }
    ]
  },
  {
    "id": "VEH-K214",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K14 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.290758357598517,
      "lng": 80.66473714615354
    },
    "routeCoords": [
      {
        "lat": 7.290758357598517,
        "lng": 80.66473714615354
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P115",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P15",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.028490596585628,
      "lng": 79.98564350945571
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.028490596585628,
        "lng": 79.98564350945571
      }
    ]
  },
  {
    "id": "VEH-P215",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P15 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.959410905548271,
      "lng": 79.99177900011604
    },
    "routeCoords": [
      {
        "lat": 6.959410905548271,
        "lng": 79.99177900011604
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K115",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K15",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.280888181186941,
      "lng": 80.68304660356368
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.280888181186941,
        "lng": 80.68304660356368
      }
    ]
  },
  {
    "id": "VEH-K215",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K15 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.282048902497944,
      "lng": 80.58424668882772
    },
    "routeCoords": [
      {
        "lat": 7.282048902497944,
        "lng": 80.58424668882772
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P116",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P16",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.0256617473802425,
      "lng": 79.8889811663633
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.0256617473802425,
        "lng": 79.8889811663633
      }
    ]
  },
  {
    "id": "VEH-P216",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P16 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.9226455000926475,
      "lng": 80.00956234301597
    },
    "routeCoords": [
      {
        "lat": 6.9226455000926475,
        "lng": 80.00956234301597
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K116",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K16",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.287609464239235,
      "lng": 80.68261390041037
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.287609464239235,
        "lng": 80.68261390041037
      }
    ]
  },
  {
    "id": "VEH-K216",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K16 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.251645653799109,
      "lng": 80.62574884222046
    },
    "routeCoords": [
      {
        "lat": 7.251645653799109,
        "lng": 80.62574884222046
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P117",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P17",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.047042301123515,
      "lng": 79.92862387917822
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.047042301123515,
        "lng": 79.92862387917822
      }
    ]
  },
  {
    "id": "VEH-P217",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P17 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.009018861216347,
      "lng": 79.98301576254487
    },
    "routeCoords": [
      {
        "lat": 7.009018861216347,
        "lng": 79.98301576254487
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K117",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K17",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.336335547268367,
      "lng": 80.6301486978845
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.336335547268367,
        "lng": 80.6301486978845
      }
    ]
  },
  {
    "id": "VEH-K217",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K17 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.339147559963073,
      "lng": 80.60403923560257
    },
    "routeCoords": [
      {
        "lat": 7.339147559963073,
        "lng": 80.60403923560257
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P118",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P18",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.923333970202698,
      "lng": 79.8981272026497
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.923333970202698,
        "lng": 79.8981272026497
      }
    ]
  },
  {
    "id": "VEH-P218",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P18 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.94758436466348,
      "lng": 79.95271268090313
    },
    "routeCoords": [
      {
        "lat": 6.94758436466348,
        "lng": 79.95271268090313
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K118",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K18",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.330657905432111,
      "lng": 80.65187478167509
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.330657905432111,
        "lng": 80.65187478167509
      }
    ]
  },
  {
    "id": "VEH-K218",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K18 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.27940139791283,
      "lng": 80.65049306510743
    },
    "routeCoords": [
      {
        "lat": 7.27940139791283,
        "lng": 80.65049306510743
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P119",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P19",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.998326647657095,
      "lng": 80.0265983211743
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.998326647657095,
        "lng": 80.0265983211743
      }
    ]
  },
  {
    "id": "VEH-P219",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P19 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.983620968134161,
      "lng": 79.96887046458887
    },
    "routeCoords": [
      {
        "lat": 6.983620968134161,
        "lng": 79.96887046458887
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K119",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K19",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.243007573457647,
      "lng": 80.65413210447035
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.243007573457647,
        "lng": 80.65413210447035
      }
    ]
  },
  {
    "id": "VEH-K219",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K19 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.306101655162509,
      "lng": 80.65013739612576
    },
    "routeCoords": [
      {
        "lat": 7.306101655162509,
        "lng": 80.65013739612576
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P120",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P20",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.00613456391101,
      "lng": 79.89504793757914
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.00613456391101,
        "lng": 79.89504793757914
      }
    ]
  },
  {
    "id": "VEH-P220",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P20 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.935842253592942,
      "lng": 79.9901747583323
    },
    "routeCoords": [
      {
        "lat": 6.935842253592942,
        "lng": 79.9901747583323
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K120",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K20",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.2626292644088855,
      "lng": 80.59218043661726
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.2626292644088855,
        "lng": 80.59218043661726
      }
    ]
  },
  {
    "id": "VEH-K220",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K20 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.268537023822685,
      "lng": 80.63471425427309
    },
    "routeCoords": [
      {
        "lat": 7.268537023822685,
        "lng": 80.63471425427309
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P121",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P21",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.061070507673765,
      "lng": 79.89480076816415
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 7.061070507673765,
        "lng": 79.89480076816415
      }
    ]
  },
  {
    "id": "VEH-P221",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P21 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.031752960534945,
      "lng": 79.97163221374774
    },
    "routeCoords": [
      {
        "lat": 7.031752960534945,
        "lng": 79.97163221374774
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K121",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K21",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.331717748204233,
      "lng": 80.5966334844918
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.331717748204233,
        "lng": 80.5966334844918
      }
    ]
  },
  {
    "id": "VEH-K221",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K21 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.324156009723154,
      "lng": 80.65330804792062
    },
    "routeCoords": [
      {
        "lat": 7.324156009723154,
        "lng": 80.65330804792062
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P122",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P22",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.961599962383668,
      "lng": 79.89143203010518
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.961599962383668,
        "lng": 79.89143203010518
      }
    ]
  },
  {
    "id": "VEH-P222",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P22 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.033948981151669,
      "lng": 79.9912286867509
    },
    "routeCoords": [
      {
        "lat": 7.033948981151669,
        "lng": 79.9912286867509
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K122",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K22",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.252243045285656,
      "lng": 80.6801077391307
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.252243045285656,
        "lng": 80.6801077391307
      }
    ]
  },
  {
    "id": "VEH-K222",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K22 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.330702589766767,
      "lng": 80.62641886931826
    },
    "routeCoords": [
      {
        "lat": 7.330702589766767,
        "lng": 80.62641886931826
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P123",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P23",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.932238257151191,
      "lng": 79.93116726123519
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.932238257151191,
        "lng": 79.93116726123519
      }
    ]
  },
  {
    "id": "VEH-P223",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P23 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 6.969623842793965,
      "lng": 80.01648818304021
    },
    "routeCoords": [
      {
        "lat": 6.969623842793965,
        "lng": 80.01648818304021
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K123",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K23",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.284079798297519,
      "lng": 80.6601959250464
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.284079798297519,
        "lng": 80.6601959250464
      }
    ]
  },
  {
    "id": "VEH-K223",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K23 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.262886207489309,
      "lng": 80.66062526868575
    },
    "routeCoords": [
      {
        "lat": 7.262886207489309,
        "lng": 80.66062526868575
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P124",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P24",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.982350951118976,
      "lng": 79.98996135299602
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.982350951118976,
        "lng": 79.98996135299602
      }
    ]
  },
  {
    "id": "VEH-P224",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P24 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.059581309380564,
      "lng": 80.01663174836105
    },
    "routeCoords": [
      {
        "lat": 7.059581309380564,
        "lng": 80.01663174836105
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K124",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K24",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.245796489336514,
      "lng": 80.61063348732557
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.245796489336514,
        "lng": 80.61063348732557
      }
    ]
  },
  {
    "id": "VEH-K224",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K24 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.305379686015496,
      "lng": 80.65755348510976
    },
    "routeCoords": [
      {
        "lat": 7.305379686015496,
        "lng": 80.65755348510976
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P125",
    "depot": "peliyagoda",
    "type": "Truck · Ambient",
    "route": "Route P25",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 6.982177189681799,
      "lng": 79.96651887037672
    },
    "routeCoords": [
      {
        "lat": 6.9654,
        "lng": 79.8821
      },
      {
        "lat": 6.982177189681799,
        "lng": 79.96651887037672
      }
    ]
  },
  {
    "id": "VEH-P225",
    "depot": "peliyagoda",
    "type": "Van · Reefer",
    "route": "Route P25 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.00924384614893,
      "lng": 79.90140487869186
    },
    "routeCoords": [
      {
        "lat": 7.00924384614893,
        "lng": 79.90140487869186
      },
      {
        "lat": 6.9654,
        "lng": 79.8821
      }
    ]
  },
  {
    "id": "VEH-K125",
    "depot": "kandy",
    "type": "Truck · Ambient",
    "route": "Route K25",
    "stops": 2,
    "status": "En Route",
    "color": "blue",
    "location": {
      "lat": 7.294690798396622,
      "lng": 80.58907454668821
    },
    "routeCoords": [
      {
        "lat": 7.2906,
        "lng": 80.6337
      },
      {
        "lat": 7.294690798396622,
        "lng": 80.58907454668821
      }
    ]
  },
  {
    "id": "VEH-K225",
    "depot": "kandy",
    "type": "Van · Reefer",
    "route": "Route K25 (Return)",
    "stops": 3,
    "status": "Returning",
    "color": "orange",
    "location": {
      "lat": 7.2585665406359166,
      "lng": 80.6796666828422
    },
    "routeCoords": [
      {
        "lat": 7.2585665406359166,
        "lng": 80.6796666828422
      },
      {
        "lat": 7.2906,
        "lng": 80.6337
      }
    ]
  },
  {
    "id": "VEH-P301",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 6.9654,
      "lng": 79.8821
    },
    "routeCoords": null
  },
  {
    "id": "VEH-K301",
    "depot": "kandy",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 7.2906,
      "lng": 80.6337
    },
    "routeCoords": null
  },
  {
    "id": "VEH-P302",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 6.9654,
      "lng": 79.8821
    },
    "routeCoords": null
  },
  {
    "id": "VEH-K302",
    "depot": "kandy",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 7.2906,
      "lng": 80.6337
    },
    "routeCoords": null
  },
  {
    "id": "VEH-P303",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 6.9654,
      "lng": 79.8821
    },
    "routeCoords": null
  },
  {
    "id": "VEH-K303",
    "depot": "kandy",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 7.2906,
      "lng": 80.6337
    },
    "routeCoords": null
  },
  {
    "id": "VEH-P304",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 6.9654,
      "lng": 79.8821
    },
    "routeCoords": null
  },
  {
    "id": "VEH-K304",
    "depot": "kandy",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 7.2906,
      "lng": 80.6337
    },
    "routeCoords": null
  },
  {
    "id": "VEH-P305",
    "depot": "peliyagoda",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 6.9654,
      "lng": 79.8821
    },
    "routeCoords": null
  },
  {
    "id": "VEH-K305",
    "depot": "kandy",
    "type": "Truck · Reefer",
    "route": "Hub Staging",
    "stops": 0,
    "status": "Dispatched",
    "color": "brand",
    "location": {
      "lat": 7.2906,
      "lng": 80.6337
    },
    "routeCoords": null
  }
];

export default function LoaderHome({ user }) {
  const currentDepot = user?.depot || 'peliyagoda';
  
  const [filter, setFilter] = useState('ALL');
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  
  // Refs for scrolling
  const listRef = useRef(null);
  const rowRefs = useRef({});
  const mapRef = useRef(null);

  // Filter categorization mapping
  const getFilterCategory = (status) => {
    if (['Dispatched', 'Ready', 'Loading'].includes(status)) return 'AT HUB';
    if (['Returning'].includes(status)) return 'RETURNING';
    return 'OUT FOR DELIVERY';
  };

  const depotVehicles = useMemo(() => 
    MOCK_VEHICLES.filter(v => v.depot === currentDepot),
  [currentDepot]);

  const filteredVehicles = useMemo(() => {
    if (filter === 'ALL') return depotVehicles;
    return depotVehicles.filter(v => getFilterCategory(v.status) === filter);
  }, [depotVehicles, filter]);

  // Handle filter changes
  useEffect(() => {
    // If the currently selected vehicle is filtered out, clear selection
    if (selectedVehicleId && !filteredVehicles.find(v => v.id === selectedVehicleId)) {
      setSelectedVehicleId(null);
    }
  }, [filter, filteredVehicles, selectedVehicleId]);

  const handleSelectVehicle = (id, fromMap = false) => {
    setSelectedVehicleId(prev => prev === id ? null : id);
    
    // Scroll the vehicle list to the row if selected from map
    if (fromMap && id && rowRefs.current[id]) {
      const row = rowRefs.current[id];
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else if (!fromMap && id && mapRef.current) {
      // Scroll the page up to the map if selected from the list
      mapRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const filterTabs = [
    { id: 'ALL', label: 'ALL' },
    { id: 'AT HUB', label: 'AT HUB' },
    { id: 'OUT FOR DELIVERY', label: 'OUT FOR DELIVERY' },
    { id: 'RETURNING', label: 'RETURNING' }
  ];

  const getEmptyStateMessage = () => {
    switch(filter) {
      case 'AT HUB': return 'No vehicles currently at the hub.';
      case 'OUT FOR DELIVERY': return 'No vehicles currently out for delivery.';
      case 'RETURNING': return 'No vehicles currently returning.';
      default: return 'No active vehicles.';
    }
  };

  return (
    <div className="p-4 sm:p-6 bg-white flex flex-col min-h-full overflow-hidden">
      
      {/* Shift Card (Top span across) */}
      <div className="shrink-0 mb-5 border border-slate-200 rounded p-4 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <h2 className="text-[15px] md:text-[16px] font-bold text-slate-900 uppercase tracking-wide">Morning Dispatch & Turnaround</h2>
          <span className="px-2.5 py-1 bg-brand-50 text-brand-700 text-[11px] font-bold rounded border border-brand-100">
            Shift Active · 03:00 AM – 11:30 AM
          </span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[13px] font-medium text-slate-500">Dispatch Progress</span>
          <span className="text-[13px] font-bold text-brand-600">8 of 14 Vehicles (57%)</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-sm overflow-hidden">
          <div className="h-full bg-brand-500 rounded-sm" style={{ width: '57%' }}></div>
        </div>
      </div>

      {/* Split Pane Container */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        
        {/* Left Pane: Controls and List */}
        <div className="w-full lg:w-[450px] flex flex-col min-h-0 shrink-0">
          {/* Active Vehicles Header & Filters */}
          <div className="shrink-0 mb-4 space-y-4">
            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <h3 className="text-[15px] md:text-[16px] font-bold text-slate-900 uppercase tracking-wide">Active Vehicles</h3>
                <span className="text-[13px] font-bold text-slate-500">· {filteredVehicles.length}</span>
              </div>
              
              <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-50 border border-slate-200 rounded shrink-0">
                {filterTabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setFilter(tab.id)}
                    className={`px-3 py-1.5 text-[11px] font-bold tracking-wider rounded transition-colors ${
                      filter === tab.id 
                        ? 'bg-white text-brand-600 shadow-sm border border-slate-200' 
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100 border border-transparent'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Vehicle List */}
          <div 
            ref={listRef}
            className="flex-1 overflow-y-auto space-y-3 pr-1 pb-4 custom-scrollbar"
          >
            {filteredVehicles.length === 0 ? (
              <div className="p-8 text-center text-[13px] text-slate-500 font-medium bg-slate-50 rounded border border-slate-100">
                {getEmptyStateMessage()}
              </div>
            ) : (
              filteredVehicles.map(veh => {
                const badgeColors = {
                  blue: 'bg-blue-50 text-blue-600',
                  orange: 'bg-orange-50 text-orange-600',
                  red: 'bg-red-50 text-red-600',
                  brand: 'bg-brand-50 text-brand-600'
                };
                
                const isSelected = selectedVehicleId === veh.id;

                return (
                  <div 
                    key={veh.id} 
                    ref={el => rowRefs.current[veh.id] = el}
                    onClick={() => handleSelectVehicle(veh.id, false)}
                    className={`border rounded p-4 flex items-start justify-between shadow-sm cursor-pointer transition-colors ${
                      isSelected ? 'border-brand-500 bg-[#F4FAF6]' : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex flex-col min-w-0 pr-4">
                      <div className="text-[14px] font-bold text-slate-900 mb-0.5">{veh.id}</div>
                      <div className="text-[12px] text-slate-500 font-medium mb-1.5">{veh.type}</div>
                      <div className="text-[13px] font-semibold text-slate-800 truncate mb-1" title={veh.route}>
                        {veh.route} {veh.stops ? `(${veh.stops} stops)` : ''}
                      </div>
                      {veh.eta && <div className="text-[12px] font-semibold text-orange-500 mt-0.5">{veh.eta}</div>}
                      {veh.action && <div className="text-[12px] font-semibold text-brand-600 mt-0.5">{veh.action}</div>}
                      {veh.desc && <div className={`text-[12px] mt-0.5 ${veh.isRedDesc ? 'font-semibold text-red-500' : 'text-slate-500'}`}>{veh.desc}</div>}
                    </div>

                    <div className="shrink-0">
                      <span className={`px-2.5 py-1 text-[11px] font-bold rounded border ${badgeColors[veh.color] || 'bg-slate-50 text-slate-600'}`}>
                        {veh.status}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: Map */}
        <div ref={mapRef} className="flex-1 h-[400px] lg:h-auto min-h-0 bg-slate-50 border border-slate-200 rounded overflow-hidden">
          <LoaderMap 
            vehicles={filteredVehicles} 
            selectedVehicleId={selectedVehicleId} 
            onSelectVehicle={(id) => handleSelectVehicle(id, true)} 
          />
        </div>

      </div>
    </div>
  );
}
