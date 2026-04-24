import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  const locale = "fr"; // Default to French; extend with cookie/header detection later

  return {
    locale,
    messages: (await import(`../../public/locales/${locale}/common.json`)).default,
  };
});
