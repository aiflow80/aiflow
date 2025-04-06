import React from "react";
import Plotly from 'plotly.js-dist-min';
import { useTheme } from '@mui/material/styles';

export const PlotComponent = ({ data, layout, config, ...rest }) => {
  const plotRef = React.useRef();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  React.useEffect(() => {
    const element = plotRef.current;
    
    if (element) {
      const themeLayout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { 
          color: theme.palette.text.primary,
          family: theme.typography.fontFamily
        },
        margin: {
          t: 10,
          r: 20,
          l: 40,
          b: 40
        },
        dragmode: 'pan',
        ...layout
      };

      // Generate colors using primary palette shades
      const plotColors = [
        theme.palette.primary[900],
        theme.palette.primary[700],
        theme.palette.primary[500],
        theme.palette.primary[300],
        theme.palette.primary[100],
        theme.palette.primary.main,
      ];

      const themedData = (data || []).map((trace, index) => ({
        ...trace,
        marker: {
          color: plotColors[index % plotColors.length],
          ...trace.marker
        }
      }));

      Plotly.newPlot(
        element, 
        themedData, 
        themeLayout, 
        {
          responsive: true,
          displayModeBar: false, 
          scrollZoom: true,  
          dragmode: 'pan',  
          editable: false,
          hovermode: 'closest'  
        }
      );

      return () => {
        if (element) {
          Plotly.purge(element);
        }
      };
    }
  }, [data, layout, config, isDark, theme]);

  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .js-plotly-plot .plotly {
        margin-top: 0 !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, [theme]);

  return <div ref={plotRef} {...rest} />;
};