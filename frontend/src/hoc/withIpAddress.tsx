const os = require('os');
export function getIpAddress() {
  const ifaces = os.networkInterfaces();

  for (const ifaceName in ifaces) {
    const iface = ifaces[ifaceName];

    for (let i = 0; i < iface.length; i++) {
      const { address, family, internal } = iface[i];

      // Check if the address is not internal (e.g., 127.0.0.1) and is IPv4
      if (!internal && family === 'IPv4') {
        return address;
      }
    }
  }

  return null;
}

export async function getServerSideProps() {
  const ipAddress = getIpAddress();

  // Pass ipAddress to the page via props
  return { props: { ipAddress: ipAddress } };
}

export function withIpAddress(Component) {
  return function WrappedComponent(props) {
    const ipAddress = getIpAddress(); // Fetch the IP address here

    // Pass the IP address to the wrapped component
    return <Component {...props} ipAddress={ipAddress} />;
  }
}

