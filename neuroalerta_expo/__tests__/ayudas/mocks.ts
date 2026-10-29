 
// Mocks compartidos por las pruebas de pantallas. Se activan con jest.mock en cada archivo de prueba.
export const mockExpoRouter = () => {
  const React = require('react');
  const router = { push: jest.fn(), replace: jest.fn(), back: jest.fn(), dismissAll: jest.fn() };
  return {
    __router: router,
    useRouter: () => router,
    useFocusEffect: (cb: () => void | (() => void)) => React.useEffect(cb, []),
  };
};
