import React from 'react';

const Container = ({ children }) => {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
      {children}
    </div>
  );
};

export default Container;
