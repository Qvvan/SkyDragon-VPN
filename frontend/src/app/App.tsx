import { RouterProvider } from 'react-router-dom'
import { Providers } from './providers'
import { router } from './router'
import { ToastContainer } from '../components/ui/Toast'

export function App() {
  return (
    <Providers>
      <RouterProvider router={router} />
      <ToastContainer />
    </Providers>
  )
}
