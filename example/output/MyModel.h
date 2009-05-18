//
//  MyModel.h
//  example

#import <Foundation/Foundation.h>


@interface MyModel : NSObject {
	NSArray *someItems;
	NSString *text;
	int count;
}


@property(assign,nonatomic) int count;

@property(retain,nonatomic) NSString* text;

@property(retain,nonatomic) NSArray* someItems;

-(id) initWithSomeItems: (NSArray*) inSomeItems text: (NSString*) inText count: (int) inCount;
@end
