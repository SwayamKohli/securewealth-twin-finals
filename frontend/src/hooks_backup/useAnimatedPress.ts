// src/hooks/useAnimatedPress.ts
import { useSharedValue, withTiming, useAnimatedStyle } from 'react-native-reanimated';

export const useAnimatedPress = (scale = 0.95, duration = 150) => {
  const scaleValue = useSharedValue(1);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scaleValue.value }],
  }));

  const onPressIn = () => {
    scaleValue.value = withTiming(scale, { duration });
  };

  const onPressOut = () => {
    scaleValue.value = withTiming(1, { duration });
  };

  return {
    animatedStyle,
    onPressIn,
    onPressOut,
  };
};