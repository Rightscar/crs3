import React from 'react';
import { Box, Typography } from '@mui/material';

interface ErrorBoundaryProps {
  // Add props
}

export const ErrorBoundary: React.FC<ErrorBoundaryProps> = (props) => {
  return (
    <Box>
      <Typography variant="h6">ErrorBoundary</Typography>
      {/* TODO: Implement component */}
    </Box>
  );
};

export default ErrorBoundary;
