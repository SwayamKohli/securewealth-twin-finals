// src/hooks/useScreenAnimation.ts
import { useEffect } from 'react';
import { useSharedValue, withTiming, useAnimatedStyle } from 'react-native-reanimated';

export const useScreenAnimation = (delay = 0) => {
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(20);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translateY.value }],
  }));

  useEffect(() => {
    const timer = setTimeout(() => {
      opacity.value = withTiming(1, { duration: 400 });
      translateY.value = withTiming(0, { duration: 300, delay: 100 });
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return animatedStyle;
};