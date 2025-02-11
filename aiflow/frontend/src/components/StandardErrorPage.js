import React from 'react';
import { Paper, Typography, Box } from '@mui/material';

const StandardErrorPage = ({ title, message, checkList }) => {
  return (
    <Box sx={{
      minHeight: '100vh',
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: 3
    }}>
      <Paper
        elevation={1}
        sx={{
          p: 3,
          maxWidth: 600,
          width: '100%',
          borderRadius: 1
        }}
      >
        <Typography variant="h5" component="h3" sx={{ mb: 2, fontWeight: 500 }}>
          {title}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {message}
        </Typography>
        {checkList && (
          <>
            <Typography sx={{ mb: 1 }}>
              Please check if:
            </Typography>
            <Box component="ul" sx={{ m: 0, pl: 3, '& li': { mt: 0.5 } }}>
              {checkList.map((item, index) => (
                <li key={index}>
                  <Typography>{item}</Typography>
                </li>
              ))}
            </Box>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default StandardErrorPage;
