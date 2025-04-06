const detectTheme = () => {
  const savedTheme = localStorage.getItem('preferred-theme');
  if (savedTheme) {
    return savedTheme;
  }
  
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const setInitialTheme = () => {
  const theme = detectTheme();
  document.documentElement.setAttribute('data-theme', theme);
  return theme;
};

export { detectTheme, setInitialTheme };
